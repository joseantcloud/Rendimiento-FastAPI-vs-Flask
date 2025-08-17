from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 2)
    @task
    def test_api(self):
        self.client.get("/test-api")