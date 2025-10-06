from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from ..middleware import CustomAuthMiddleware
from ..models import UserSession, Role, UserRole
import jwt
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class FixedMiddlewareTests(APITestCase):
    def setUp(self):
        # Создаем роль пользователя
        self.user_role, _ = Role.objects.get_or_create(name='user')

    def test_middleware_with_valid_token(self):
        """Тест middleware с валидным токеном"""
        # Создаем пользователя
        user = User.objects.create_user(
            email='middleware_test@test.com',
            password='test123'
        )
        UserRole.objects.get_or_create(user=user, role=self.user_role)

        # Создаем сессию
        expires_at = timezone.now() + timedelta(days=1)
        session = UserSession.objects.create(
            user=user,
            expires_at=expires_at,
            is_active=True
        )

        # Создаем JWT токен вручную
        payload = {
            'session_id': str(session.id),
            'user_id': user.id,
            'email': user.email,
            'exp': expires_at,
            'iat': timezone.now()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        # Делаем запрос с токеном
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('profile'))

        # Должен быть успешный доступ
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_middleware_with_invalid_token(self):
        """Тест middleware с невалидным токеном"""
        # Делаем запрос с невалидным токеном
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get(reverse('profile'))

        # Должна быть ошибка 401 (Unauthorized), а не 403
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_middleware_without_token(self):
        """Тест middleware без токена"""
        response = self.client.get(reverse('profile'))

        # Должна быть ошибка 401 (Unauthorized), а не 403
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_middleware_with_expired_token(self):
        """Тест middleware с истекшим токеном"""
        # Создаем пользователя
        user = User.objects.create_user(
            email='expired_test@test.com',
            password='test123'
        )
        UserRole.objects.get_or_create(user=user, role=self.user_role)

        # Создаем истекший токен
        expired_payload = {
            'session_id': 'fake-session-id',
            'user_id': user.id,
            'email': user.email,
            'exp': timezone.now() - timedelta(days=1),  # Истекшая дата
            'iat': timezone.now() - timedelta(days=2)
        }
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm='HS256')

        # Делаем запрос с истекшим токеном
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
        response = self.client.get(reverse('profile'))

        # Должна быть ошибка 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_middleware_public_endpoints(self):
        """Тест что публичные эндпоинты работают без аутентификации"""
        # Тестируем логин (публичный эндпоинт)
        response = self.client.post(reverse('login'), {
            'email': 'nonexistent@test.com',
            'password': 'wrongpass'
        })
        # Должен вернуть 401 из-за неправильных учетных данных, а не из-за middleware
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Тестируем регистрацию (публичный эндпоинт)
        response = self.client.post(reverse('register'), {
            'email': 'newuser@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        })
        # Должен обработать запрос (201 или 400), а не блокировать middleware
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])