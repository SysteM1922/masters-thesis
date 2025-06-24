import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SERVER_IP = "10.255.40.73"
#SERVER_IP = "192.168.1.207"
TEST_API_URL = f"https://{SERVER_IP}:8000/v1/tests/"
VERIFY_SSL = False

class TestsAPI:

    @staticmethod
    def create_test(test_type, house_id, division):
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
    def update_test(test_id, start_time, notes=""):
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
    def get_tests(test_id, house_id):
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
    def delete_test(test_id):
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
    def add_measurement(test_id, timestamp, point):
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
        
    @staticmethod
    def add_measurement_bulk(test_id, results_list):
        try:
            response = requests.post(
                f"{TEST_API_URL}measurement/bulk",
                json={
                    "test_id": test_id,
                    "measurements": results_list,
                },
                verify=VERIFY_SSL
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error adding measurement to test {test_id}: {e}")
            return False