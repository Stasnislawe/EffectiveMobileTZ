import uuid
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from ..models import User, Role, UserRole


class BasicFunctionalityTests(APITestCase):
    """Простые тесты базовой функциональности без сложных setup"""

    def test_user_registration(self):
        """Тест регистрации пользователя"""
        register_data = {
            'email': f'test_{uuid.uuid4().hex}@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(reverse('register'), register_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_login(self):
        """Тест входа пользователя"""
        # Создаем пользователя напрямую с уникальным email
        email = f'login_test_{uuid.uuid4().hex}@example.com'
        user = User.objects.create_user(
            email=email,
            password='testpass123',
            first_name='Login',
            last_name='Test'
        )

        # Назначаем роль
        user_role, _ = Role.objects.get_or_create(name='user')
        UserRole.objects.get_or_create(user=user, role=user_role)

        # Теперь логинимся
        login_data = {
            'email': email,
            'password': 'testpass123'
        }
        response = self.client.post(reverse('login'), login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_protected_endpoint_without_auth(self):
        """Тест доступа к защищенному endpoint без аутентификации"""
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)