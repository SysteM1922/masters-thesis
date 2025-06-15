import requests
import urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TEST_API_URL = "https://10.255.40.73:8000/v1/tests/"
VERIFY_SSL = False

class TestsAPI:

    @staticmethod
    def create_test(test_type: str, house_id: str, division: int):
        try:
            response = requests.post(
                TEST_API_URL,
                json={
                    "test_type": test_type,
                    "houseID": house_id,
                    "division": division
                },
                verify=VERIFY_SSL
            )
            response.raise_for_status()
            return response.json().get("test_id", None)
        except requests.RequestException as e:
            print(f"Error creating test: {e}")
            return None
        
    @staticmethod
    def update_test(test_id: str, notes: str, start_time: datetime):
        try:
            response = requests.patch(
                TEST_API_URL,
                json={
                    "test_id": test_id,
                    "notes": notes,
                    "start_time": start_time
                },
                verify=VERIFY_SSL
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error updating test {test_id}: {e}")
            return False
        
    @staticmethod
    def get_tests(test_id: str, house_id: str):
        try:
            response = requests.get(
                TEST_API_URL,
                params={
                    "test_id": test_id,
                    "houseID": house_id
                },
                verify=VERIFY_SSL
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching tests: {e}")
            return None
    
    @staticmethod    
    def delete_test(test_id: str):
        try:
            response = requests.delete(
                TEST_API_URL,
                params={"test_id": test_id},
                verify=VERIFY_SSL
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error deleting test {test_id}: {e}")
            return False
        
    @staticmethod
    def add_measurement(test_id: str, timestamp: datetime, point: str):
        try:
            response = requests.post(
                f"{TEST_API_URL}measurement",
                json={
                    "test_id": test_id,
                    "timestamp": timestamp,
                    "point": point
                },
                verify=VERIFY_SSL
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error adding measurement to test {test_id}: {e}")
            return False


if __name__ == "__main__":
    test_id = TestsAPI.delete_test("test0003")
    print(f"Created test with ID: {test_id}")