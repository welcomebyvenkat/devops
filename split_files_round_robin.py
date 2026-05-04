from pathlib import Path
from collections import defaultdict

input_file = Path("input_3gb.txt")
output_dir = Path("split_output")
output_dir.mkdir(exist_ok=True)

num_parts = 10   # change this: how many files you want

# Open output files
writers = [
    open(output_dir / f"part_{i+1:03d}.txt", "w", encoding="utf-8", newline="")
    for i in range(num_parts)
]

# Tracks next output file for each record type
type_counter = defaultdict(int)

try:
    with open(input_file, "r", encoding="utf-8", errors="replace") as infile:
        for line in infile:
            line = line.rstrip("\n")

            if not line:
                continue

            # First column before pipe = record type
            record_type = line.split("|", 1)[0]

            # Round-robin separately for each record type
            part_index = type_counter[record_type] % num_parts

            writers[part_index].write(line + "\n")

            type_counter[record_type] += 1

finally:
    for w in writers:
        w.close()

print("Split completed")
print("Record counts by type:")
for record_type, count in sorted(type_counter.items(), key=lambda x: int(x[0])):
    print(record_type, count)
