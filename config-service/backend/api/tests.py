from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from api.models import User


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create(
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
        )
        self.assertEqual(user.first_name, "Alice")
        self.assertEqual(user.last_name, "Smith")
        self.assertEqual(user.email, "alice@example.com")

    def test_str_representation(self):
        user = User.objects.create(
            first_name="Bob",
            last_name="Jones",
            email="bob@example.com",
        )
        self.assertEqual(str(user), "Bob Jones")


class UserAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        self.user = User.objects.create(**self.user_data)

    def test_list_users(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["first_name"], "Alice")
        self.assertEqual(response.data[0]["last_name"], "Smith")
        self.assertEqual(response.data[0]["email"], "alice@example.com")

    def test_create_user(self):
        new_user = {
            "first_name": "Charlie",
            "last_name": "Brown",
            "email": "charlie@example.com",
        }
        response = self.client.post("/api/users/", new_user, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(response.data["first_name"], "Charlie")

    def test_retrieve_user(self):
        response = self.client.get(f"/api/users/{self.user.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "alice@example.com")

    def test_update_user(self):
        updated = {
            "first_name": "Alicia",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        response = self.client.put(
            f"/api/users/{self.user.id}/", updated, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alicia")

    def test_delete_user(self):
        response = self.client.delete(f"/api/users/{self.user.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 0)
