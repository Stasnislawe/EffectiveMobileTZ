from django.core.management.base import BaseCommand
from ...models import User, Role, BusinessElement, AccessRoleRule, UserRole
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными для демонстрации системы'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных...')

        # 1. Создаем роли
        admin_role, _ = Role.objects.get_or_create(
            name='admin',
            defaults={'description': 'Полный доступ ко всему', 'is_system': True}
        )
        manager_role, _ = Role.objects.get_or_create(
            name='manager',
            defaults={'description': 'Управление товарами и заказами', 'is_system': False}
        )
        user_role, _ = Role.objects.get_or_create(
            name='user',
            defaults={'description': 'Обычный пользователь', 'is_system': False}
        )

        # 2. Создаем бизнес-элементы
        elements = {}
        business_data = [
            ('users', 'Управление пользователями', 'administration'),
            ('products', 'Товары и каталог', 'business'),
            ('orders', 'Заказы и продажи', 'business'),
            ('access_rules', 'Правила доступа', 'system'),
        ]

        for name, description, category in business_data:
            element, _ = BusinessElement.objects.get_or_create(
                name=name,
                defaults={'description': description, 'category': category}
            )
            elements[name] = element

        # 3. Правила доступа - исправленные названия полей
        access_rules = [
            # Админ - все права на все
            (admin_role, elements['users'], {
                'read_all_permission': True,
                'create_permission': True,
                'update_all_permission': True,
                'delete_all_permission': True,
                'read_own_permission': True,
                'update_own_permission': True,
                'delete_own_permission': True,
            }),
            (admin_role, elements['products'], {
                'read_all_permission': True,
                'create_permission': True,
                'update_all_permission': True,
                'delete_all_permission': True,
                'read_own_permission': True,
                'update_own_permission': True,
                'delete_own_permission': True,
            }),
            (admin_role, elements['orders'], {
                'read_all_permission': True,
                'create_permission': True,
                'update_all_permission': True,
                'delete_all_permission': True,
                'read_own_permission': True,
                'update_own_permission': True,
                'delete_own_permission': True,
            }),
            (admin_role, elements['access_rules'], {
                'read_all_permission': True,
                'create_permission': True,
                'update_all_permission': True,
                'delete_all_permission': True,
                'read_own_permission': True,
                'update_own_permission': True,
                'delete_own_permission': True,
            }),

            # Менеджер
            (manager_role, elements['users'], {
                'read_all_permission': True,
                'create_permission': False,
                'update_all_permission': False,
                'delete_all_permission': False
            }),
            (manager_role, elements['products'], {
                'read_all_permission': True,
                'create_permission': True,
                'update_all_permission': True,
                'delete_all_permission': False
            }),
            (manager_role, elements['orders'], {
                'read_all_permission': True,
                'create_permission': True,
                'update_all_permission': True,
                'delete_all_permission': False
            }),

            # Пользователь
            (user_role, elements['products'], {
                'read_own_permission': True,
                'create_permission': True,
                'update_own_permission': True,
                'delete_own_permission': True
            }),
            (user_role, elements['orders'], {
                'read_own_permission': True,
                'create_permission': True,
                'update_own_permission': True,
                'delete_own_permission': False
            }),
        ]

        for role, element, permissions in access_rules:
            AccessRoleRule.objects.get_or_create(
                role=role,
                element=element,
                defaults=permissions
            )

        # 4. Создаем тестовых пользователей с правильным назначением ролей
        test_users = [
            {'email': 'admin@company.com', 'password': 'Admin123!', 'first_name': 'Алексей', 'last_name': 'Петров',
             'role': admin_role},
            {'email': 'manager@company.com', 'password': 'Manager123!', 'first_name': 'Мария', 'last_name': 'Сидорова',
             'role': manager_role},
            {'email': 'user1@company.com', 'password': 'User123!', 'first_name': 'Иван', 'last_name': 'Иванов',
             'role': user_role},
            {'email': 'user2@company.com', 'password': 'User123!', 'first_name': 'Ольга', 'last_name': 'Кузнецова',
             'role': user_role},
            {'email': 'user3@company.com', 'password': 'User123!', 'first_name': 'Дмитрий', 'last_name': 'Смирнов',
             'role': user_role},
        ]

        created_users = {}
        for user_data in test_users:
            email = user_data['email']

            # Создаем или получаем пользователя
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name']
                }
            )

            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f'Создан пользователь: {email}')
            else:
                # Если пользователь уже существует, обновляем пароль
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f'Обновлен пользователь: {email}')

            # Удаляем существующие роли пользователя (чтобы избежать дублирования)
            UserRole.objects.filter(user=user).delete()

            # Создаем новую связь с ролью
            UserRole.objects.create(
                user=user,
                role=user_data['role'],
                assigned_by=user
            )

            created_users[email] = user

        # 5. Создаем тестовые сессии
        for user in created_users.values():
            if not user.sessions.exists():
                user.sessions.create(
                    expires_at=timezone.now() + timedelta(days=7)
                )
                self.stdout.write(f'Создана сессия для: {user.email}')

        self.stdout.write(
            self.style.SUCCESS('\n✅ Тестовые данные созданы!\n') +
            '👤 Данные для входа:\n' +
            'Админ: admin@company.com / Admin123!\n' +
            'Менеджер: manager@company.com / Manager123!\n' +
            'Пользователи: user1@company.com / User123! (и user2, user3)\n\n' +
            '🔗 API эндпоинты для тестирования:\n' +
            '   POST /api/auth/login/     - Вход в систему\n' +
            '   GET  /api/products/       - Список товаров\n' +
            '   GET  /api/orders/         - Список заказов\n' +
            '   GET  /api/users/          - Список пользователей\n' +
            '   GET  /api/auth/profile/   - Профиль пользователя\n'
        )