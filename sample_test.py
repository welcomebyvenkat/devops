import argparse
import asyncio
import csv
import json
import os
import random
import time
from typing import Dict, Any, Optional

import aiohttp


def build_payload(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Payload matches your Postman template.
    CSV must have columns:
      ExternalMemberID, VisibleID, NoteText
    """
    external_member_id = (row.get("ExternalMemberID") or "").strip()
    visible_id = (row.get("VisibleID") or "").strip()
    note_text = (row.get("NoteText") or "").strip()

    return {
        "memberIdType": "External",
        "noteDefinitionVisibleId": visible_id,
        "noteType": "admin",
        "notes": [
            {
                "memberId": external_member_id,
                "noteFields": [],
                "noteText": note_text,
            }
        ],
    }


def parse_returned_id(resp_json: Any, external_member_id: str) -> Optional[str]:
    """
    If response format is:
      { "data": { "<ExternalMemberID>": ["returnedId"] }, "success": true/false, ... }
    """
    try:
        if isinstance(resp_json, dict):
            data = resp_json.get("data")
            if isinstance(data, dict):
                arr = data.get(external_member_id)
                if isinstance(arr, list) and arr:
                    rid = arr[0]
                    if rid in (None, "null", ""):
                        return None
                    return str(rid)
    except Exception:
        pass
    return None


async def post_one(
    session: aiohttp.ClientSession,
    url: str,
    headers: Dict[str, str],
    row: Dict[str, str],
    timeout_s: int,
    retries: int,
    backoff_base_s: float,
) -> Dict[str, Any]:
    external_member_id = (row.get("ExternalMemberID") or "").strip()
    payload = build_payload(row)

    last_error = ""
    for attempt in range(retries + 1):
        try:
            t0 = time.time()
            async with session.post(url, json=payload, headers=headers, timeout=timeout_s) as resp:
                status = resp.status
                body_text = await resp.text()
                elapsed_ms = int((time.time() - t0) * 1000)

                # Non-2xx -> capture real reason
                if not (200 <= status < 300):
                    last_error = f"HTTP {status} body={body_text[:500]}"
                    if status in (408, 429, 500, 502, 503, 504) and attempt < retries:
                        await asyncio.sleep(backoff_base_s * (2 ** attempt) + random.uniform(0, 0.25))
                        continue
                    return {
                        "ok": False,
                        "ExternalMemberID": external_member_id,
                        "httpStatus": status,
                        "elapsed_ms": elapsed_ms,
                        "returnedId": "",
                        "error": last_error,
                    }

                # Try parse JSON
                try:
                    resp_json = json.loads(body_text)
                except Exception:
                    resp_json = {"raw": body_text}

                returned_id = parse_returned_id(resp_json, external_member_id)
                success_flag = resp_json.get("success") if isinstance(resp_json, dict) else None

                # If API explicitly says success=false treat as failure
                if success_flag is False:
                    last_error = f"success=false body={body_text[:500]}"
                    return {
                        "ok": False,
                        "ExternalMemberID": external_member_id,
                        "httpStatus": status,
                        "elapsed_ms": elapsed_ms,
                        "returnedId": returned_id or "",
                        "error": last_error,
                    }

                return {
                    "ok": True,
                    "ExternalMemberID": external_member_id,
                    "httpStatus": status,
                    "elapsed_ms": elapsed_ms,
                    "returnedId": returned_id or "",
                    "error": "",
                }

        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            if attempt < retries:
                await asyncio.sleep(backoff_base_s * (2 ** attempt) + random.uniform(0, 0.25))
                continue
            return {
                "ok": False,
                "ExternalMemberID": external_member_id,
                "httpStatus": "",
                "elapsed_ms": "",
                "returnedId": "",
                "error": last_error,
            }

    # Final safety return (never return None)
    return {
        "ok": False,
        "ExternalMemberID": external_member_id,
        "httpStatus": "",
        "elapsed_ms": "",
        "returnedId": "",
        "error": last_error or "Unknown error",
    }


async def run_all(args):
    # Read CSV
    with open(args.input, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("No rows found in input CSV.")
        return

    # Ensure output dirs exist
    os.makedirs(os.path.dirname(args.out_success) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(args.out_failed) or ".", exist_ok=True)

    # Headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"

    # SSL handling: --verify-false disables cert validation (TEST ONLY)
    ssl_param = False if args.verify_false else None

    connector = aiohttp.TCPConnector(ssl=ssl_param, limit=args.concurrency)
    sem = asyncio.Semaphore(args.concurrency)

    success_fields = ["ExternalMemberID", "httpStatus", "elapsed_ms", "returnedId"]
    failed_fields = ["ExternalMemberID", "httpStatus", "elapsed_ms", "error"]

    with open(args.out_success, "w", newline="", encoding="utf-8") as sf, \
         open(args.out_failed, "w", newline="", encoding="utf-8") as ff:

        sw = csv.DictWriter(sf, fieldnames=success_fields)
        fw = csv.DictWriter(ff, fieldnames=failed_fields)
        sw.writeheader()
        fw.writeheader()

        started = time.time()
        done = okc = failc = 0

        async with aiohttp.ClientSession(connector=connector) as session:

            async def bound_call(r):
                async with sem:
                    return await post_one(
                        session=session,
                        url=args.url,
                        headers=headers,
                        row=r,
                        timeout_s=args.timeout,
                        retries=args.retries,
                        backoff_base_s=args.backoff,
                    )

            # NOTE: for very large files, this creates many tasks at once.
            # If you run into memory issues, tell me — I'll give the batching/queue version.
            tasks = [asyncio.create_task(bound_call(r)) for r in rows]

            for coro in asyncio.as_completed(tasks):
                res = await coro
                done += 1

                if res.get("ok"):
                    okc += 1
                    sw.writerow({
                        "ExternalMemberID": res.get("ExternalMemberID", ""),
                        "httpStatus": res.get("httpStatus", ""),
                        "elapsed_ms": res.get("elapsed_ms", ""),
                        "returnedId": res.get("returnedId", ""),
                    })
                else:
                    failc += 1
                    fw.writerow({
                        "ExternalMemberID": res.get("ExternalMemberID", ""),
                        "httpStatus": res.get("httpStatus", ""),
                        "elapsed_ms": res.get("elapsed_ms", ""),
                        "error": res.get("error", ""),
                    })

                # ✅ Progress print with % + elapsed + ETA
                if done % args.print_every == 0 or done == len(rows):
                    elapsed = time.time() - started
                    percent = (done / len(rows)) * 100
                    rps = done / elapsed if elapsed else 0

                    remaining = len(rows) - done
                    eta_sec = remaining / rps if rps > 0 else 0

                    print(
                        f"Progress: {done}/{len(rows)} "
                        f"({percent:.1f}%) | "
                        f"ok={okc} fail={failc} | "
                        f"elapsed={elapsed/60:.1f} min | "
                        f"ETA={eta_sec/60:.1f} min"
                    )

        total = time.time() - started
        print("\nDONE")
        print(f"total={len(rows)} ok={okc} fail={failc} time={total/60:.1f} min")
        print("success file:", args.out_success)
        print("failed file :", args.out_failed)


def main():
    p = argparse.ArgumentParser(description="Read CSV and POST concurrently (with progress + ETA)")
    p.add_argument("--input", required=True, help="Input CSV path")
    p.add_argument("--url", required=True, help="API URL")
    p.add_argument("--token", default=None, help="Bearer token (optional)")
    p.add_argument("--concurrency", type=int, default=5, help="Concurrent requests")
    p.add_argument("--timeout", type=int, default=120, help="Timeout per request (seconds)")
    p.add_argument("--retries", type=int, default=1, help="Retries for transient errors")
    p.add_argument("--backoff", type=float, default=0.5, help="Backoff base seconds")
    p.add_argument("--out-success", default="success.csv", help="Success output CSV")
    p.add_argument("--out-failed", default="failed.csv", help="Failed output CSV")
    p.add_argument("--verify-false", action="store_true", help="Disable SSL verification (TEST ONLY)")
    p.add_argument("--print-every", type=int, default=25, help="Print progress every N records")
    args = p.parse_args()

    asyncio.run(run_all(args))


if __name__ == "__main__":
    main()
