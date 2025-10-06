import uuid
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from ..models import User, Role, UserRole


class ErrorHandlingTests(APITestCase):
    """Тесты обработки ошибок"""

    def setUp(self):
        # Создаем или получаем роль 'user'
        self.user_role, _ = Role.objects.get_or_create(name='user')

        # Используем уникальный email для каждого теста
        self.email = f'testuser_{uuid.uuid4().hex}@example.com'
        self.user = User.objects.create_user(
            email=self.email,
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Используем get_or_create чтобы избежать дублирования
        UserRole.objects.get_or_create(user=self.user, role=self.user_role)

        # Логинимся и сохраняем токен
        login_response = self.client.post(reverse('login'), {
            'email': self.email,
            'password': 'testpass123'
        })
        self.token = login_response.data['token']

    def test_401_unauthorized_access(self):
        """Тест 401 ошибки при доступе без аутентификации"""
        # Не устанавливаем заголовок Authorization
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token_401(self):
        """Тест 401 ошибки при невалидном токене"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_here')
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_403_forbidden_access(self):
        """Тест 403 ошибки при отсутствии прав доступа"""
        # Создаем пользователя без прав на управление пользователями
        regular_email = f'regular_{uuid.uuid4().hex}@example.com'
        regular_user = User.objects.create_user(
            email=regular_email,
            password='regular123',
            first_name='Regular',
            last_name='User'
        )
        UserRole.objects.get_or_create(user=regular_user, role=self.user_role)

        # Логинимся как обычный пользователь
        login_response = self.client.post(reverse('login'), {
            'email': regular_email,
            'password': 'regular123'
        })
        token = login_response.data['token']

        # Пытаемся получить доступ к управлению пользователями
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('users'))

        # Должны получить 403, так как у обычного пользователя нет прав на просмотр всех пользователей
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_expired_token_401(self):
        """Тест 401 ошибки при истекшем токене"""
        # Создаем истекший токен вручную
        import jwt
        from django.conf import settings
        from django.utils import timezone
        from datetime import datetime

        expired_payload = {
            'session_id': 'fake-session-id',
            'user_id': self.user.id,
            'email': self.user.email,
            'exp': datetime(2020, 1, 1, tzinfo=timezone.utc),  # Прошедшая дата
            'iat': timezone.now()
        }
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm='HS256')

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)