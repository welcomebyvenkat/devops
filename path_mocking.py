#my_module.py
import requests

class Database:
    def get_data(self):
        return "real DB data"

def fetch_and_store():
    response = requests.get("https://example.com/api")
    api_data = response.json()
    
    db = Database()
    db_data = db.get_data()

    return {"api": api_data, "db": db_data}

#------------- Using Multiple patch Decorators
from unittest.mock import patch, MagicMock
import unittest
import my_module

class TestFetchAndStore(unittest.TestCase):
    @patch("my_module.requests.get")
    @patch("my_module.Database.get_data")
    def test_fetch_and_store(self, mock_get_data, mock_requests_get):
        # Mock API response
        mock_requests_get.return_value.json.return_value = {"message": "mocked API data"}
        
        # Mock DB response
        mock_get_data.return_value = "mocked DB data"

        # Call the function under test
        result = my_module.fetch_and_store()

        # Assertions
        self.assertEqual(result["api"], {"message": "mocked API data"})
        self.assertEqual(result["db"], "mocked DB data")

        # Ensure API and DB calls were made
        mock_requests_get.assert_called_once_with("https://example.com/api")
        mock_get_data.assert_called_once()

if __name__ == "__main__":
    unittest.main()
#--------------Using patch as a Context Manager
def test_fetch_and_store():
    with patch("my_module.requests.get") as mock_requests_get, \
         patch("my_module.Database.get_data") as mock_get_data:

        # Mock API response
        mock_requests_get.return_value.json.return_value = {"message": "mocked API data"}

        # Mock DB response
        mock_get_data.return_value = "mocked DB data"

        # Call the function under test
        result = my_module.fetch_and_store()

        # Assertions
        assert result["api"] == {"message": "mocked API data"}
        assert result["db"] == "mocked DB data"

        # Ensure API and DB calls were made
        mock_requests_get.assert_called_once_with("https://example.com/api")
        mock_get_data.assert_called_once()

#--------------- Example Without patch
from unittest.mock import MagicMock
import unittest
import my_module

class TestFetchAndStore(unittest.TestCase):
    def test_fetch_and_store(self):
        # Create mock objects
        mock_requests = MagicMock()
        mock_requests.json.return_value = {"message": "mocked API data"}

        mock_db = MagicMock()
        mock_db.get_data.return_value = "mocked DB data"

        # Manually replace the real objects with mocks
        my_module.requests.get = MagicMock(return_value=mock_requests)  # Mock API call
        my_module.Database = MagicMock(return_value=mock_db)  # Mock DB class

        # Call the function under test
        result = my_module.fetch_and_store()

        # Assertions
        self.assertEqual(result["api"], {"message": "mocked API data"})
        self.assertEqual(result["db"], "mocked DB data")

        # Ensure API and DB calls were made
        my_module.requests.get.assert_called_once_with("https://example.com/api")
        mock_db.get_data.assert_called_once()

if __name__ == "__main__":
    unittest.main()
#--------------------- Test with Fixtures and responses (test_my_module.py)
import pytest
import responses
from unittest.mock import MagicMock
import my_module

@pytest.fixture
def mock_api():
    """Fixture to mock the external API call"""
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "https://example.com/api",
            json={"message": "mocked API data"},
            status=200
        )
        yield rsps  # Provide mocked API response to test functions

@pytest.fixture
def mock_db():
    """Fixture to mock the Database class"""
    mock_db_instance = MagicMock()
    mock_db_instance.get_data.return_value = "mocked DB data"
    
    original_db_class = my_module.Database  # Save original class
    my_module.Database = MagicMock(return_value=mock_db_instance)  # Mock class
    
    yield mock_db_instance  # Provide mock instance to test functions

    my_module.Database = original_db_class  # Restore original class after tests

@pytest.fixture
def mock_fetch_and_store(mock_api, mock_db):
    """Fixture to mock both API and DB for fetch_and_store()"""
    return my_module.fetch_and_store  # Return function with mocks applied

def test_fetch_and_store_success(mock_fetch_and_store):
    """Test fetch_and_store() with a successful API and DB response"""
    result = mock_fetch_and_store()
    
    assert result["api"] == {"message": "mocked API data"}
    assert result["db"] == "mocked DB data"

def test_fetch_and_store_empty_api(mock_api, mock_fetch_and_store):
    """Test fetch_and_store() when API returns empty data"""
    mock_api.replace(
        responses.GET,
        "https://example.com/api",
        json={},  # Simulating an empty API response
        status=200
    )

    result = mock_fetch_and_store()
    
    assert result["api"] == {}  # Expect empty API response
    assert result["db"] == "mocked DB data"  # DB remains the same


