from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

User = get_user_model()


class DiagnosticTests(APITestCase):
    """Диагностические тесты для выявления проблем с аутентификацией"""

    def test_user_creation_and_password(self):
        """Тест создания пользователя и проверки пароля"""
        print("\n=== Диагностика создания пользователя ===")

        # Создаем пользователя напрямую
        user = User.objects.create_user(
            email='diagnostic@test.com',
            password='testpass123',
            first_name='Diagnostic',
            last_name='User'
        )

        print(f"Создан пользователь: {user.email}")
        print(f"Пароль в БД: {user.password}")
        print(f"is_active: {user.is_active}")

        # Проверяем пароль
        password_check = user.check_password('testpass123')
        print(f"Проверка пароля 'testpass123': {password_check}")

        self.assertTrue(password_check)
        self.assertTrue(user.is_active)

    def test_login_diagnostic(self):
        """Диагностика процесса логина"""
        print("\n=== Диагностика логина ===")

        # Создаем пользователя
        user = User.objects.create_user(
            email='login_test@test.com',
            password='testpass123'
        )
        print(f"Создан пользователь для логина: {user.email}")

        # Пытаемся залогиниться
        login_data = {
            'email': 'login_test@test.com',
            'password': 'testpass123'
        }

        print(f"Данные для логина: {login_data}")
        response = self.client.post(reverse('login'), login_data)

        print(f"Статус ответа: {response.status_code}")
        print(f"Данные ответа: {response.data}")

        if response.status_code != 200:
            print("=== ДЕТАЛИ ОШИБКИ ===")
            print(f"Пользователь в БД: {User.objects.filter(email='login_test@test.com').exists()}")
            if User.objects.filter(email='login_test@test.com').exists():
                db_user = User.objects.get(email='login_test@test.com')
                print(f"is_active в БД: {db_user.is_active}")
                print(f"Проверка пароля в БД: {db_user.check_password('testpass123')}")