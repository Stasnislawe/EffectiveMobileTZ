import uuid
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from ..models import User, Role, UserRole, BusinessElement, AccessRoleRule


class PermissionTests(APITestCase):
    """Тесты системы прав доступа"""

    def setUp(self):
        # Создаем тестовые роли
        self.admin_role, _ = Role.objects.get_or_create(name='admin')
        self.user_role, _ = Role.objects.get_or_create(name='user')

        # Создаем бизнес-элементы если их нет
        self.products_element, _ = BusinessElement.objects.get_or_create(name='products')
        self.users_element, _ = BusinessElement.objects.get_or_create(name='users')

        # Создаем правила доступа для админа
        AccessRoleRule.objects.get_or_create(
            role=self.admin_role,
            element=self.products_element,
            defaults={
                'read_all_permission': True,
                'read_own_permission': True,
                'create_permission': True,
                'update_all_permission': True,
                'update_own_permission': True,
                'delete_all_permission': True,
                'delete_own_permission': True,
                'can_export': True,
                'can_import': True
            }
        )

        # Создаем правила доступа для обычного пользователя
        AccessRoleRule.objects.get_or_create(
            role=self.user_role,
            element=self.products_element,
            defaults={
                'read_all_permission': False,
                'read_own_permission': True,  # Может читать свои продукты
                'create_permission': False,
                'update_all_permission': False,
                'update_own_permission': False,
                'delete_all_permission': False,
                'delete_own_permission': False,
                'can_export': False,
                'can_import': False
            }
        )

        # Создаем тестовых пользователей с уникальными email
        self.admin_user = User.objects.create_user(
            email=f'admin_{uuid.uuid4().hex}@test.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        UserRole.objects.get_or_create(user=self.admin_user, role=self.admin_role)

        self.regular_user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex}@test.com',
            password='userpass123',
            first_name='Regular',
            last_name='User'
        )
        UserRole.objects.get_or_create(user=self.regular_user, role=self.user_role)

    def test_admin_access_to_products(self):
        """Тест доступа админа к продуктам"""
        # Логинимся как админ
        login_data = {'email': self.admin_user.email, 'password': 'adminpass123'}
        response = self.client.post(reverse('login'), login_data)

        # Проверяем успешный логин
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

        token = response.data['token']

        # Делаем запрос к продуктам с токеном
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('products'))

        # Админ должен видеть все продукты (3 продукта)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_user_access_to_products(self):
        """Тест доступа обычного пользователя к продуктам"""
        # Логинимся как обычный пользователь
        login_data = {'email': self.regular_user.email, 'password': 'userpass123'}
        response = self.client.post(reverse('login'), login_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

        token = response.data['token']

        # Делаем запрос к продуктам с токеном
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('products'))

        # Обычный пользователь должен видеть только свои продукты (1 продукт)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        # Проверяем, что это действительно продукт текущего пользователя
        self.assertEqual(response.data[0]['owner_id'], self.regular_user.id)
        self.assertEqual(response.data[0]['name'], 'Планшет')  # Конкретный продукт

    def test_admin_access_to_users(self):
        """Тест доступа админа к управлению пользователями"""
        # Логинимся как админ
        login_data = {'email': self.admin_user.email, 'password': 'adminpass123'}
        response = self.client.post(reverse('login'), login_data)
        token = response.data['token']

        # Создаем правило доступа для админа к users
        AccessRoleRule.objects.get_or_create(
            role=self.admin_role,
            element=self.users_element,
            defaults={
                'read_all_permission': True,
                'read_own_permission': True,
                'create_permission': True,
                'update_all_permission': True,
                'update_own_permission': True,
                'delete_all_permission': True,
                'delete_own_permission': True,
                'can_export': True,
                'can_import': True
            }
        )

        # Делаем запрос к управлению пользователями с токеном
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('users'))

        # Админ должен видеть всех пользователей
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Должно быть как минимум 2 пользователя (admin + regular)
        self.assertGreaterEqual(len(response.data), 2)

    def test_user_access_to_users_forbidden(self):
        """Тест что обычный пользователь не может управлять пользователями"""
        # Логинимся как обычный пользователь
        login_data = {'email': self.regular_user.email, 'password': 'userpass123'}
        response = self.client.post(reverse('login'), login_data)
        token = response.data['token']

        # У обычного пользователя нет прав на управление пользователями
        AccessRoleRule.objects.get_or_create(
            role=self.user_role,
            element=self.users_element,
            defaults={
                'read_all_permission': False,
                'read_own_permission': False,  # Не может даже читать
                'create_permission': False,
                'update_all_permission': False,
                'update_own_permission': False,
                'delete_all_permission': False,
                'delete_own_permission': False,
                'can_export': False,
                'can_import': False
            }
        )

        # Делаем запрос к управлению пользователями с токеном
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('users'))

        # Обычный пользователь не должен иметь доступ
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)