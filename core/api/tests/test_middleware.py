from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from ..middleware import CustomAuthMiddleware

User = get_user_model()


class MiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = CustomAuthMiddleware(lambda r: None)

    def test_middleware_import(self):
        """Тест что middleware можно импортировать"""
        try:
            from ..middleware import CustomAuthMiddleware
            middleware = CustomAuthMiddleware(lambda r: None)
            self.assertIsNotNone(middleware)
        except ImportError as e:
            self.fail(f"Не удалось импортировать middleware: {e}")


class MiddlewareIntegrationTests(APITestCase):
    def test_middleware_in_settings(self):
        """Тест что middleware добавлена в настройки"""
        from django.conf import settings
        middleware_found = any(
            'CustomAuthMiddleware' in middleware or
            'core.api.middleware' in middleware
            for middleware in settings.MIDDLEWARE
        )
        self.assertTrue(middleware_found, "CustomAuthMiddleware не найдена в settings.MIDDLEWARE")

    def test_middleware_sets_user(self):
        """Тест что middleware устанавливает request.user"""
        # Создаем пользователя и сессию
        user = User.objects.create_user(
            email='middleware@test.com',
            password='middleware123'
        )

        # Создаем сессию и токен
        session = user.sessions.create()
        token = session.create_jwt_token()

        # Делаем запрос с токеном
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('profile'))

        # Должен быть успешный доступ
        self.assertEqual(response.status_code, status.HTTP_200_OK)