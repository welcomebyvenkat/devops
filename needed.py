'''
from collections import defaultdict
from typing import Dict, TypedDict


class TableDetails(TypedDict):
    id: int
    name: str


RequestsData = Dict[str, Dict[str, TableDetails]]

data: RequestsData = defaultdict(dict)
data["request_id_1"]["tablename"] = {"id": 1, "name": "test"}
data["request_id_1"]["tablename2"] = {"id": 100, "name": "next details"}
data["request_id_2"]["tablename2"] = {"id": 100, "name": "next details"}
data["request_id_5"]["tablename2"] = {"id": 100, "name": "next details"}

for k,v in data.items():
    print(k)
    print(v)

raise Exception('test')
testDict:Dict[str,str] = {"a":"b","b":{}}
print(testDict)
'''
from lib.sample_file import f_method
from typing import Tuple,Dict,List,TypedDict
class SetParameters:
    def __init__(self,test):
        self.hai = "hai"
        self.passwd = f_method("a","b",test)
        self.passwd2 = f_method("a", "b", "ccc")
def f_dm_call(param: Tuple[str,SetParameters])->str:
    (value,params) = param
    if(value == "hai"):
        return params.passwd2
    else:
        return params.passwd

print(f_dm_call(("hai1",SetParameters("hello"))))





#--------------------
import pytest
from unittest.mock import patch
from typedict_sample import SetParameters, f_dm_call  # Import the class and function to test

@patch("typedict_sample.f_method")  # Mock f_method
def test_f_dm_call(mock_f_method):
    # Ensure f_method always returns "mocked_passwd"
    mock_f_method.return_value = "mocked_passwd"

    # Create an instance of SetParameters, which calls the mocked f_method
    params = SetParameters("hello")

    # Ensure the passwd attribute is set to the mocked return value
    assert params.passwd == "mocked_passwd"

    # Test case where value is "hai" (should return "0")
    result1 = f_dm_call(("hai", params))
    assert result1 == "mocked_passwd"

    # Test case where value is NOT "hai" (should return mocked_passwd)
    result2 = f_dm_call(("hai1", params))
    assert result2 == "mocked_passwd"  # Correct expectation

    # Verify that f_method was called exactly once with expected arguments
    mock_f_method.assert_any_call("a", "b", "hello")
    #mock_f_method.assert_any_call("a", "b", "hello")



'''
import pytest
from unittest.mock import patch
from lib.sample_file import f_method  # Import the function to be mocked
from typedict_sample import SetParameters, f_dm_call  # Import the class and function to test

# Mock f_method to return a fixed value
@patch("lib.sample_file.f_method", return_value="mocked_passwd")
def test_f_dm_call(mock_f_method):
    # Create a SetParameters instance with the mock
    params = SetParameters("hello")

    # Test case where value is "hai"
    #result1 = f_dm_call(("hai", params))
    #assert result1 == "0"  # Should return "0" when value is "hai"

    # Test case where value is not "hai"
    result2 = f_dm_call(("hai1", params))
    assert result2 == "mocked_passwd"  # Should return the mocked password

    # Ensure f_method was called once
    #mock_f_method.assert_called_once_with("a", "b", "hello")
'''

#---------------------
import pytest
from unittest.mock import patch
from typedict_sample import SetParameters, f_dm_call  # Import the class and function to test

# Fixture to mock f_method
@pytest.fixture
@patch("typedict_sample.f_method", return_value="mocked_passwd1")  # Mocking f_method
def params_fixture(mock_f_method):
    params = SetParameters("hello")  # Calls f_method (which is mocked)
    return params  # Returns an instance of SetParameters with mocked passwd

# Fixture to return the tuple ("hai", params)
@pytest.fixture
def tuple_fixture(params_fixture):
    return ("hai", params_fixture)  # Returns tuple with string and SetParameters instance


#@patch("typedict_sample.f_method")  # Mock f_method
def test_f_dm_call(params_fixture,tuple_fixture):
    # Ensure f_method always returns "mocked_passwd"
    #mock_f_method.return_value = "mocked_passwd"

    # Create an instance of SetParameters, which calls the mocked f_method
    #params = SetParameters("hello")

    # Ensure the passwd attribute is set to the mocked return value
    #assert params.passwd == "mocked_passwd"

    # Test case where value is "hai" (should return "0")
    result1 = f_dm_call(tuple_fixture)
    assert result1 == "mocked_passwd1"

    # Test case where value is NOT "hai" (should return mocked_passwd)
    result2 = f_dm_call(("hai1", params_fixture))
    assert result2 == "mocked_passwd1"  # Correct expectation

    # Verify that f_method was called exactly once with expected arguments
    #mock_f_method.assert_called_once_with("a", "b", "hello")



'''
import pytest
from unittest.mock import patch
from lib.sample_file import f_method  # Import the function to be mocked
from typedict_sample import SetParameters, f_dm_call  # Import the class and function to test

# Mock f_method to return a fixed value
@patch("lib.sample_file.f_method", return_value="mocked_passwd")
def test_f_dm_call(mock_f_method):
    # Create a SetParameters instance with the mock
    params = SetParameters("hello")

    # Test case where value is "hai"
    #result1 = f_dm_call(("hai", params))
    #assert result1 == "0"  # Should return "0" when value is "hai"

    # Test case where value is not "hai"
    result2 = f_dm_call(("hai1", params))
    assert result2 == "mocked_passwd"  # Should return the mocked password

    # Ensure f_method was called once
    #mock_f_method.assert_called_once_with("a", "b", "hello")
'''

