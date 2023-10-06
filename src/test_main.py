from fastapi.testclient import TestClient

from main import app

class TestMyApp:
    @classmethod
    def setup_class(cls):
        cls.data = {}
        cls.client = TestClient(app)

    def test_create_city(self):
        response = self.client.post("/create-city/", json={"name": "Kazan"})
        assert response.status_code == 200
        city_id = response.json()["id"]
        self.data["city_id"] = city_id
        print("City ID:", city_id)

    def test_get_cities_none_q(self):
        response = self.client.get('/get-cities/')
        assert response.status_code == 200

    def test_get_cities_with_q(self):
        response = self.client.get('/get-cities/?q=Kazan')
        assert response.status_code == 200

    def test_register_user(self):
        response = self.client.post('/register-user/', json={'name': 'TEST', 'surname': 'TEST', 'age': 100})
        assert response.status_code == 200
        user_id = response.json()["id"]
        self.data["user_id"] = user_id
        print("User ID:", user_id)

    def test_users_list(self):
        response = self.client.get('/users-list/')
        assert response.status_code == 200

    def test_picnic_add(self):
        response = self.client.post('/picnic-add/',
                                    json={'city_id': self.data["city_id"], "datetime": "2023-10-19T13:00:00"})
        assert response.status_code == 200
        picnic_id = response.json()["id"]
        self.data["picnic_id"] = picnic_id
        print("Picnic ID:", picnic_id)

    def test_all_picnic(self):
        response = self.client.get('/all-picnics/')
        assert response.status_code == 200

    def test_picnic_register(self):
        response = self.client.post('/picnic-register/',
                                    json={"user_id": self.data["user_id"], "picnic_id": self.data["picnic_id"]})
        assert response.status_code == 200
