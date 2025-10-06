import uuid
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class SimpleAuthTest(APITestCase):
    """Простые тесты аутентификации"""

    def test_register_and_login(self):
        """Тест регистрации и входа"""
        # Используем уникальный email для каждого теста
        unique_email = f'simple_{uuid.uuid4().hex}@test.com'

        # 1. Регистрация
        register_data = {
            'email': unique_email,
            'password': 'Simple123!',  # Более сложный пароль
            'password_confirm': 'Simple123!',
            'first_name': 'Simple',
            'last_name': 'User'
        }

        response = self.client.post(reverse('register'), register_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 2. Логин
        login_data = {
            'email': unique_email,
            'password': 'Simple123!'
        }

        response = self.client.post(reverse('login'), login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

        token = response.data['token']

        # 3. Доступ к профилю с токеном
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)