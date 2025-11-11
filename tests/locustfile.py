from locust import HttpUser, task, between
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OpenBMCUser(HttpUser):
    host = "https://localhost:2443"
    wait_time = between(0.5, 1)

    @task(2)
    def get_system_info(self):
        self.client.get("/redfish/v1/Systems/system", auth=("root", "0penBmc"), verify=False, name="OpenBMC /Systems/system")

    @task(1)
    def get_power_state(self):
        with self.client.get("/redfish/v1/Systems/system", auth=("root", "0penBmc"), verify=False, catch_response=True, name="OpenBMC /Systems/system") as response:
            if response.status_code == 200:
                power_state = response.json().get("PowerState", "Unknown")
                print(f"PowerState: {power_state}")
                response.success()
            else:
                response.failure("Не удалось получить PowerState")


class PublicAPITestUser(HttpUser):
    host = ""
    wait_time = between(0.5, 1)

    @task(3)
    def get_posts(self):
        self.client.get("https://jsonplaceholder.typicode.com/posts", name="JSONPlaceholder /posts")
    
