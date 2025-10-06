# core/api/tests/test_complete_scenarios.py
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from ..models import User, Role, BusinessElement, AccessRoleRule, UserRole


class CompleteSystemTests(APITestCase):
    def setUp(self):
        # Очищаем все перед тестом
        UserRole.objects.all().delete()
        User.objects.all().delete()
        Role.objects.all().delete()
        BusinessElement.objects.all().delete()
        AccessRoleRule.objects.all().delete()

        # Временно отключаем сигнал
        from django.db.models.signals import post_save
        from ..models import set_default_role
        post_save.disconnect(set_default_role, sender=User)

        # Создаем роли
        self.admin_role = Role.objects.create(name='admin')
        self.user_role = Role.objects.create(name='user')

        # Бизнес-элементы
        self.users_element = BusinessElement.objects.create(name='users')
        self.products_element = BusinessElement.objects.create(name='products')
        self.orders_element = BusinessElement.objects.create(name='orders')

        # Правила доступа для админа
        AccessRoleRule.objects.create(
            role=self.admin_role,
            element=self.users_element,
            read_all_permission=True,
            create_permission=True,
            update_all_permission=True,
            delete_all_permission=True
        )

        AccessRoleRule.objects.create(
            role=self.admin_role,
            element=self.products_element,
            read_all_permission=True,
            create_permission=True,
            update_all_permission=True,
            delete_all_permission=True
        )

        # Правила доступа для пользователя (только свои продукты)
        AccessRoleRule.objects.create(
            role=self.user_role,
            element=self.products_element,
            read_own_permission=True,
            create_permission=True,
            update_own_permission=True
        )

        # Создаем пользователей с явным назначением ролей
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        UserRole.objects.create(user=self.admin_user, role=self.admin_role)

        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='user123',
            first_name='Regular',
            last_name='User'
        )
        UserRole.objects.create(user=self.regular_user, role=self.user_role)

        # Включаем сигнал обратно
        post_save.connect(set_default_role, sender=User)

    def test_admin_full_access(self):
        """Тест полного доступа администратора"""
        # Логиним админа
        login_response = self.client.post(reverse('login'), {
            'email': 'admin@test.com',
            'password': 'admin123'
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        token = login_response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Проверяем доступ ко всем endpoints
        response = self.client.get(reverse('users'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_limited_access(self):
        """Тест ограниченного доступа обычного пользователя"""
        # Логиним обычного пользователя
        login_response = self.client.post(reverse('login'), {
            'email': 'user@test.com',
            'password': 'user123'
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        token = login_response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Должен иметь доступ к products
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # НЕ должен иметь доступ к users (403)
        response = self.client.get(reverse('users'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_registration_flow(self):
        """Тест полного цикла регистрации и аутентификации"""
        # Регистрация
        register_data = {
            'email': 'newuser@test.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(reverse('register'), register_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Логин
        login_response = self.client.post(reverse('login'), {
            'email': 'newuser@test.com',
            'password': 'newpass123'
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('token', login_response.data)

        # Доступ к защищенным ресурсам
        token = login_response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.get(reverse('products'))
        # Новый пользователь должен иметь доступ к products (сигнал назначил роль user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)