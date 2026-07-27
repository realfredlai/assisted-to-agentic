from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from api.models import Application, Configuration, User


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


class ApplicationModelTest(TestCase):
    def test_create_application(self):
        app = Application.objects.create(name="Payments", app_type="web")
        self.assertEqual(app.name, "Payments")
        self.assertEqual(app.app_type, "web")

    def test_str_representation(self):
        app = Application.objects.create(name="Payments", app_type="web")
        self.assertEqual(str(app), "Payments")

    def test_delete_application_cascades_configurations(self):
        app = Application.objects.create(name="Payments", app_type="web")
        Configuration.objects.create(application=app, name="default")
        app.delete()
        self.assertEqual(Configuration.objects.count(), 0)

    def test_delete_user_leaves_application_in_place(self):
        user = User.objects.create(
            first_name="Alice", last_name="Smith", email="alice@example.com"
        )
        app = Application.objects.create(name="Payments", app_type="web")
        app.users.add(user)
        user.delete()
        app.refresh_from_db()
        self.assertEqual(Application.objects.count(), 1)
        self.assertEqual(app.users.count(), 0)


class ConfigurationModelTest(TestCase):
    def setUp(self):
        self.app = Application.objects.create(name="Payments", app_type="web")

    def test_create_configuration_defaults_settings_to_empty_dict(self):
        config = Configuration.objects.create(application=self.app, name="default")
        self.assertEqual(config.dev_settings, {})
        self.assertEqual(config.uat_settings, {})
        self.assertEqual(config.prod_settings, {})

    def test_str_representation(self):
        config = Configuration.objects.create(application=self.app, name="default")
        self.assertEqual(str(config), "Payments/default")

    def test_duplicate_configuration_name_in_same_application_raises(self):
        Configuration.objects.create(application=self.app, name="default")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Configuration.objects.create(application=self.app, name="default")

    def test_same_configuration_name_in_different_application_allowed(self):
        Configuration.objects.create(application=self.app, name="default")
        other_app = Application.objects.create(name="Billing", app_type="cloud")
        config = Configuration.objects.create(application=other_app, name="default")
        self.assertEqual(config.name, "default")
        self.assertEqual(Configuration.objects.filter(name="default").count(), 2)


class ApplicationAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create(
            first_name="Alice", last_name="Smith", email="alice@example.com"
        )
        self.user2 = User.objects.create(
            first_name="Bob", last_name="Jones", email="bob@example.com"
        )
        self.app = Application.objects.create(name="Payments", app_type="web")

    def test_list_applications_ordered_by_name(self):
        Application.objects.create(name="Analytics", app_type="cloud")
        response = self.client.get("/api/applications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.data]
        self.assertEqual(names, sorted(names))
        self.assertIn("Payments", names)
        self.assertIn("Analytics", names)

    def test_create_application_valid(self):
        new_app = {"name": "Billing", "app_type": "cloud"}
        response = self.client.post("/api/applications/", new_app, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.count(), 2)
        self.assertEqual(response.data["name"], "Billing")

    def test_create_application_duplicate_name(self):
        new_app = {"name": "Payments", "app_type": "cloud"}
        response = self.client.post("/api/applications/", new_app, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Application.objects.count(), 1)

    def test_create_application_invalid_app_type(self):
        new_app = {"name": "Billing", "app_type": "not-a-real-type"}
        response = self.client.post("/api/applications/", new_app, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Application.objects.count(), 1)

    def test_create_application_with_users(self):
        new_app = {
            "name": "Billing",
            "app_type": "cloud",
            "users": [self.user1.id, self.user2.id],
        }
        response = self.client.post("/api/applications/", new_app, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Application.objects.get(name="Billing")
        self.assertEqual(
            set(created.users.values_list("id", flat=True)),
            {self.user1.id, self.user2.id},
        )

    def test_create_application_unknown_user_id(self):
        new_app = {"name": "Billing", "app_type": "cloud", "users": [999999]}
        response = self.client.post("/api/applications/", new_app, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Application.objects.count(), 1)

    def test_retrieve_application(self):
        response = self.client.get(f"/api/applications/{self.app.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Payments")

    def test_patch_application_users(self):
        self.app.users.add(self.user1)
        response = self.client.patch(
            f"/api/applications/{self.app.id}/",
            {"users": [self.user2.id]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.app.refresh_from_db()
        self.assertEqual(
            set(self.app.users.values_list("id", flat=True)), {self.user2.id}
        )

    def test_delete_application_removes_its_configurations(self):
        Configuration.objects.create(application=self.app, name="default")
        response = self.client.delete(f"/api/applications/{self.app.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Application.objects.count(), 0)
        self.assertEqual(Configuration.objects.count(), 0)


class ConfigurationAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.app = Application.objects.create(name="Payments", app_type="web")
        self.other_app = Application.objects.create(name="Billing", app_type="cloud")
        self.config = Configuration.objects.create(
            application=self.app, name="default"
        )

    def test_nested_list_returns_only_that_applications_configurations(self):
        Configuration.objects.create(application=self.other_app, name="default")
        response = self.client.get(
            f"/api/applications/{self.app.id}/configurations/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "default")
        self.assertEqual(response.data[0]["application"], self.app.id)

    def test_create_configuration_settings_omitted_default_empty(self):
        new_config = {"name": "staging"}
        response = self.client.post(
            f"/api/applications/{self.app.id}/configurations/",
            new_config,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["dev_settings"], {})
        self.assertEqual(response.data["uat_settings"], {})
        self.assertEqual(response.data["prod_settings"], {})

    def test_create_configuration_non_object_settings_rejected(self):
        new_config = {"name": "staging", "dev_settings": [1, 2]}
        response = self.client.post(
            f"/api/applications/{self.app.id}/configurations/",
            new_config,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            Configuration.objects.filter(application=self.app, name="staging").count(),
            0,
        )

    def test_create_configuration_duplicate_name_same_application(self):
        new_config = {"name": "default"}
        response = self.client.post(
            f"/api/applications/{self.app.id}/configurations/",
            new_config,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            Configuration.objects.filter(application=self.app, name="default").count(),
            1,
        )

    def test_create_configuration_same_name_under_another_application(self):
        new_config = {"name": "default"}
        response = self.client.post(
            f"/api/applications/{self.other_app.id}/configurations/",
            new_config,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Configuration.objects.filter(
                application=self.other_app, name="default"
            ).count(),
            1,
        )

    def test_retrieve_configuration(self):
        response = self.client.get(
            f"/api/applications/{self.app.id}/configurations/{self.config.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["application"], self.app.id)

    def test_update_configuration_settings(self):
        put_body = {
            "name": "default",
            "dev_settings": {"debug": True},
        }
        response = self.client.put(
            f"/api/applications/{self.app.id}/configurations/{self.config.id}/",
            put_body,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.config.refresh_from_db()
        self.assertEqual(self.config.dev_settings, {"debug": True})

        patch_response = self.client.patch(
            f"/api/applications/{self.app.id}/configurations/{self.config.id}/",
            {"uat_settings": {"debug": False}},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.config.refresh_from_db()
        self.assertEqual(self.config.uat_settings, {"debug": False})

    def test_delete_configuration(self):
        response = self.client.delete(
            f"/api/applications/{self.app.id}/configurations/{self.config.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Configuration.objects.count(), 0)

    def test_unknown_application_id_404_for_list_and_create(self):
        list_response = self.client.get("/api/applications/999999/configurations/")
        self.assertEqual(list_response.status_code, status.HTTP_404_NOT_FOUND)

        create_response = self.client.post(
            "/api/applications/999999/configurations/",
            {"name": "default"},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_configuration_under_wrong_application_404(self):
        response = self.client.get(
            f"/api/applications/{self.other_app.id}/configurations/{self.config.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
