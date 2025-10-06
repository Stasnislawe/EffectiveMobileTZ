from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
import bcrypt
import jwt


class UserManager(BaseUserManager):
    """
    Кастомный менеджер пользователей с поддержкой email-аутентификации.

    Наследует стандартные методы Django с добавлением кастомной логики
    для работы с email как основным идентификатором.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Создает и сохраняет пользователя с указанным email и паролем.

        Args:
            email (str): Email пользователя (используется как username)
            password (str, optional): Пароль пользователя
            **extra_fields: Дополнительные поля пользователя

        Returns:
            User: Созданный объект пользователя

        Raises:
            ValueError: Если email не указан
        """
        if not email:
            raise ValueError('Email обязателен для создания пользователя')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        if password:
            user.set_password(password)

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Создает суперпользователя с расширенными правами.

        Args:
            email (str): Email суперпользователя
            password (str, optional): Пароль суперпользователя
            **extra_fields: Дополнительные поля

        Returns:
            User: Созданный объект суперпользователя
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Основная модель пользователя системы.

    Заменяет стандартную модель User Django, предоставляя кастомные поля
    и методы для управления аутентификацией и авторизацией согласно ТЗ.

    Attributes:
        email (EmailField): Уникальный email пользователя (используется как USERNAME_FIELD)
        first_name (CharField): Имя пользователя
        last_name (CharField): Фамилия пользователя
        middle_name (CharField): Отчество пользователя
        is_active (BooleanField): Флаг активности аккаунта
        deleted_at (DateTimeField): Время мягкого удаления (соответствует ТЗ)
        is_staff (BooleanField): Флаг доступа к админке Django
        is_superuser (BooleanField): Флаг суперпользователя Django
        created_at (DateTimeField): Время создания пользователя
        updated_at (DateTimeField): Время последнего обновления
    """

    email = models.EmailField(
        unique=True,
        db_index=True,
        verbose_name="Email",
        help_text="Уникальный email пользователя, используется для входа в систему"
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Имя",
        help_text="Имя пользователя"
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Фамилия",
        help_text="Фамилия пользователя"
    )
    middle_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Отчество",
        help_text="Отчество пользователя"
    )

    # Статусы согласно ТЗ
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
        help_text="Отметьте, если пользователь может входить в систему"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата удаления",
        help_text="Дата и время мягкого удаления пользователя"
    )

    # Django стандартные поля для совместимости
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Staff статус",
        help_text="Определяет, может ли пользователь входить в админку Django"
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name="Superuser статус",
        help_text="Определяет, имеет ли пользователь все права без явного назначения"
    )

    # Временные метки
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name="Дата создания",
        help_text="Дата и время создания учетной записи"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
        help_text="Дата и время последнего обновления учетной записи"
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['is_active', 'deleted_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        """Строковое представление пользователя."""
        return self.email

    def soft_delete(self):
        """
        Выполняет мягкое удаление пользователя согласно ТЗ.

        Устанавливает флаг is_active=False, записывает время удаления
        и инвалидирует все активные сессии пользователя.
        """
        self.is_active = False
        self.deleted_at = timezone.now()

        # Инвалидируем все активные сессии
        self.sessions.filter(is_active=True).update(is_active=False)
        self.save()

    def create_session(self):
        """
        Создает новую сессию пользователя и возвращает JWT токен.

        Returns:
            str: JWT токен для аутентификации
        """
        session = UserSession.objects.create(user=self)
        return session.create_jwt_token()

    @property
    def full_name(self):
        """Возвращает полное имя пользователя."""
        name_parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(part for part in name_parts if part).strip()

    @property
    def role(self):
        """Возвращает первую роль пользователя (для обратной совместимости)"""
        user_role = self.user_roles.first()
        return user_role.role if user_role else None

    @property
    def roles(self):
        """Возвращает все роли пользователя"""
        return [ur.role for ur in self.user_roles.all()]


class UserSession(models.Model):
    """
    Модель для управления сессиями пользователей.

    Обеспечивает механизм JWT + сессии в БД для контроля доступа
    и возможности принудительного разлогинивания.

    Attributes:
        id (UUIDField): Уникальный идентификатор сессии
        user (ForeignKey): Ссылка на пользователя
        is_active (BooleanField): Флаг активности сессии
        created_at (DateTimeField): Время создания сессии
        expires_at (DateTimeField): Время истечения сессии
        last_activity_at (DateTimeField): Время последней активности
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID сессии",
        help_text="Уникальный идентификатор сессии"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name="Пользователь",
        help_text="Пользователь, к которому относится сессия"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна",
        help_text="Отметьте, если сессия активна"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания",
        help_text="Дата и время создания сессии"
    )
    expires_at = models.DateTimeField(
        verbose_name="Дата истечения",
        help_text="Дата и время истечения срока действия сессии"
    )
    last_activity_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Последняя активность",
        help_text="Дата и время последней активности в сессии"
    )

    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'Сессия пользователя'
        verbose_name_plural = 'Сессии пользователей'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at', 'is_active']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        """Строковое представление сессии."""
        return f"Сессия {self.user.email} ({self.created_at})"

    def save(self, *args, **kwargs):
        """Сохраняет сессию, устанавливая expires_at по умолчанию."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    def create_jwt_token(self):
        """
        Создает JWT токен для сессии.

        Returns:
            str: Закодированный JWT токен
        """
        payload = {
            'session_id': str(self.id),
            'user_id': self.user.id,
            'email': self.user.email,
            'exp': self.expires_at,
            'iat': timezone.now(),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    def is_expired(self):
        """
        Проверяет, истекла ли сессия.

        Returns:
            bool: True если сессия истекла, иначе False
        """
        return timezone.now() > self.expires_at

    def deactivate(self):
        """Деактивирует сессию (используется при logout)."""
        self.is_active = False
        self.save()


class RevokedToken(models.Model):
    """
    Модель для blacklist JWT токенов.

    Позволяет отзывать JWT токены до истечения их срока действия
    для реализации полноценного logout и безопасности.

    Attributes:
        jti (CharField): JWT ID (уникальный идентификатор токена)
        revoked_at (DateTimeField): Время отзыва токена
        expires_at (DateTimeField): Время истечения токена
    """

    jti = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="JWT ID",
        help_text="Уникальный идентификатор JWT токена"
    )
    revoked_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Время отзыва",
        help_text="Дата и время отзыва токена"
    )
    expires_at = models.DateTimeField(
        verbose_name="Время истечения",
        help_text="Дата и время истечения срока действия токена"
    )

    class Meta:
        db_table = 'revoked_tokens'
        verbose_name = 'Отозванный токен'
        verbose_name_plural = 'Отозванные токены'
        indexes = [
            models.Index(fields=['jti']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        """Строковое представление отозванного токена."""
        return f"Отозванный токен {self.jti}"

    def is_valid(self):
        """
        Проверяет, действителен ли еще отзыв токена.

        Returns:
            bool: True если токен все еще должен считаться отозванным
        """
        return timezone.now() < self.expires_at


class Role(models.Model):
    """
    Модель ролей пользователей в системе.

    Определяет группы пользователей с общими правами доступа.
    Системные роли (is_system=True) защищены от удаления через UI.

    Attributes:
        name (CharField): Уникальное название роли
        description (TextField): Описание роли
        is_system (BooleanField): Флаг системной роли
        created_at (DateTimeField): Время создания роли
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название роли",
        help_text="Уникальное название роли (admin, manager, user, etc.)"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
        help_text="Подробное описание роли и её назначения"
    )
    is_system = models.BooleanField(
        default=False,
        verbose_name="Системная роль",
        help_text="Отметьте для системных ролей, которые нельзя удалять"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name="Дата создания",
        help_text="Дата и время создания роли"
    )

    class Meta:
        db_table = 'roles'
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'
        ordering = ['name']

    def __str__(self):
        """Строковое представление роли."""
        return self.name


class UserRole(models.Model):
    """
    M2M связь пользователей и ролей с дополнительными полями.

    Позволяет назначать пользователям несколько ролей с отслеживанием
    времени назначения и пользователя, выполнившего назначение.

    Attributes:
        user (ForeignKey): Ссылка на пользователя
        role (ForeignKey): Ссылка на роль
        assigned_at (DateTimeField): Время назначения роли
        assigned_by (ForeignKey): Пользователь, назначивший роль
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name="Пользователь",
        help_text="Пользователь, которому назначена роль"
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_users',
        verbose_name="Роль",
        help_text="Роль, назначенная пользователю"
    )
    assigned_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Время назначения",
        help_text="Дата и время назначения роли пользователю"
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_roles',
        verbose_name="Назначивший",
        help_text="Пользователь, который выполнил назначение роли"
    )

    class Meta:
        db_table = 'user_roles'
        verbose_name = 'Роль пользователя'
        verbose_name_plural = 'Роли пользователей'
        unique_together = ('user', 'role')
        indexes = [
            models.Index(fields=['user', 'role']),
        ]
        ordering = ['-assigned_at']

    def __str__(self):
        """Строковое представление назначения роли."""
        return f"{self.user.email} - {self.role.name}"


class BusinessElement(models.Model):
    """
    Модель бизнес-элементов (ресурсов) системы.

    Определяет модули или сущности приложения, к которым может быть
    предоставлен доступ (пользователи, товары, заказы и т.д.).

    Attributes:
        name (CharField): Уникальное название элемента
        description (TextField): Описание элемента
        category (CharField): Категория для группировки элементов
        created_at (DateTimeField): Время создания элемента
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название элемента",
        help_text="Уникальное название бизнес-элемента (users, products, orders, etc.)"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
        help_text="Подробное описание назначения бизнес-элемента"
    )
    category = models.CharField(
        max_length=100,
        default='general',
        verbose_name="Категория",
        help_text="Категория для группировки бизнес-элементов"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name="Дата создания",
        help_text="Дата и время создания бизнес-элемента"
    )

    class Meta:
        db_table = 'business_elements'
        verbose_name = 'Бизнес-элемент'
        verbose_name_plural = 'Бизнес-элементы'
        indexes = [
            models.Index(fields=['name', 'category']),
        ]
        ordering = ['category', 'name']

    def __str__(self):
        """Строковое представление бизнес-элемента."""
        return f"{self.name} ({self.category})"


class AccessRoleRule(models.Model):
    """
    Основная модель правил доступа согласно ТЗ.

    Связывает роли и бизнес-элементы, определяя конкретные права доступа
    с четким разделением на "глобальные права" и "права на свои объекты".

    Attributes:
        role (ForeignKey): Роль, к которой применяется правило
        element (ForeignKey): Бизнес-элемент, к которому предоставляется доступ

        # Глобальные права (на ВСЕ объекты)
        read_all_permission (BooleanField): Чтение всех объектов
        create_permission (BooleanField): Создание новых объектов
        update_all_permission (BooleanField): Редактирование всех объектов
        delete_all_permission (BooleanField): Удаление всех объектов

        # Права на СВОИ объекты
        read_own_permission (BooleanField): Чтение своих объектов
        update_own_permission (BooleanField): Редактирование своих объектов
        delete_own_permission (BooleanField): Удаление своих объектов

        # Дополнительные права
        can_export (BooleanField): Экспорт данных
        can_import (BooleanField): Импорт данных

        # Временные метки
        created_at (DateTimeField): Время создания правила
        updated_at (DateTimeField): Время последнего обновления
    """

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='access_rules',
        verbose_name="Роль",
        help_text="Роль, для которой определяется правило доступа"
    )
    element = models.ForeignKey(
        BusinessElement,
        on_delete=models.CASCADE,
        related_name='access_rules',
        verbose_name="Бизнес-элемент",
        help_text="Бизнес-элемент, к которому предоставляется доступ"
    )

    # === ГЛОБАЛЬНЫЕ ПРАВА (на ВСЕ объекты) ===
    read_all_permission = models.BooleanField(
        default=False,
        verbose_name="Чтение всех объектов",
        help_text="Разрешает чтение ЛЮБЫХ объектов этого типа"
    )
    create_permission = models.BooleanField(
        default=False,
        verbose_name="Создание объектов",
        help_text="Разрешает создание новых объектов этого типа"
    )
    update_all_permission = models.BooleanField(
        default=False,
        verbose_name="Редактирование всех объектов",
        help_text="Разрешает редактирование ЛЮБЫХ объектов этого типа"
    )
    delete_all_permission = models.BooleanField(
        default=False,
        verbose_name="Удаление всех объектов",
        help_text="Разрешает удаление ЛЮБЫХ объектов этого типа"
    )

    # === ПРАВА НА СВОИ ОБЪЕКТЫ ===
    read_own_permission = models.BooleanField(
        default=False,
        verbose_name="Чтение своих объектов",
        help_text="Разрешает чтение только СВОИХ объектов этого типа"
    )
    update_own_permission = models.BooleanField(
        default=False,
        verbose_name="Редактирование своих объектов",
        help_text="Разрешает редактирование только СВОИХ объектов этого типа"
    )
    delete_own_permission = models.BooleanField(
        default=False,
        verbose_name="Удаление своих объектов",
        help_text="Разрешает удаление только СВОИХ объектов этого типа"
    )

    # === ДОПОЛНИТЕЛЬНЫЕ ПРАВА ===
    can_export = models.BooleanField(
        default=False,
        verbose_name="Экспорт данных",
        help_text="Разрешает экспорт данных этого типа"
    )
    can_import = models.BooleanField(
        default=False,
        verbose_name="Импорт данных",
        help_text="Разрешает импорт данных этого типа"
    )

    # Временные метки
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name="Дата создания",
        help_text="Дата и время создания правила доступа"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
        help_text="Дата и время последнего обновления правила доступа"
    )

    class Meta:
        db_table = 'access_roles_rules'
        verbose_name = 'Правило доступа'
        verbose_name_plural = 'Правила доступа'
        unique_together = ['role', 'element']
        indexes = [
            models.Index(fields=['role', 'element']),
        ]
        ordering = ['role', 'element']

    def __str__(self):
        """Строковое представление правила доступа."""
        return f"{self.role.name} → {self.element.name}"

    def has_global_permission(self, action):
        """
        Проверяет глобальное разрешение на действие.

        Args:
            action (str): Действие для проверки ('read', 'create', 'update', 'delete', 'export', 'import')

        Returns:
            bool: True если глобальное разрешение есть, иначе False
        """
        action_map = {
            'read': self.read_all_permission,
            'create': self.create_permission,
            'update': self.update_all_permission,
            'delete': self.delete_all_permission,
            'export': self.can_export,
            'import': self.can_import,
        }
        return action_map.get(action, False)

    def has_own_permission(self, action):
        """
        Проверяет разрешение на действие над собственными объектами.

        Args:
            action (str): Действие для проверки ('read', 'update', 'delete')

        Returns:
            bool: True если разрешение на свои объекты есть, иначе False
        """
        action_map = {
            'read': self.read_own_permission,
            'update': self.update_own_permission,
            'delete': self.delete_own_permission,
        }
        return action_map.get(action, False)

    def get_permissions_summary(self):
        """
        Возвращает сводку всех прав в структурированном виде.

        Returns:
            dict: Словарь с группировкой прав по категориям
        """
        return {
            'global': {
                'read': self.read_all_permission,
                'create': self.create_permission,
                'update': self.update_all_permission,
                'delete': self.delete_all_permission,
            },
            'own': {
                'read': self.read_own_permission,
                'update': self.update_own_permission,
                'delete': self.delete_own_permission,
            },
            'additional': {
                'export': self.can_export,
                'import': self.can_import,
            }
        }




class Resource(models.Model):
    """
    Модель ресурсов для object-level permissions (опционально).

    Предоставляет механизм ACL для особых случаев, когда требуется
    тонкая настройка прав доступа к конкретным объектам.

    Attributes:
        content_type (CharField): Тип бизнес-объекта
        object_id (PositiveIntegerField): ID конкретного объекта
        owner (ForeignKey): Владелец ресурса
        metadata (JSONField): Дополнительные метаданные
        created_at (DateTimeField): Время создания ресурса
    """

    content_type = models.CharField(
        max_length=100,
        verbose_name="Тип контента",
        help_text="Тип бизнес-объекта (project, order, product, etc.)"
    )
    object_id = models.PositiveIntegerField(
        verbose_name="ID объекта",
        help_text="ID конкретного бизнес-объекта"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_resources',
        verbose_name="Владелец",
        help_text="Пользователь, который владеет этим ресурсом"
    )
    metadata = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Метаданные",
        help_text="Дополнительные метаданные ресурса в формате JSON"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name="Дата создания",
        help_text="Дата и время создания записи ресурса"
    )

    class Meta:
        db_table = 'resources'
        verbose_name = 'Ресурс'
        verbose_name_plural = 'Ресурсы'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['owner', 'content_type']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        """Строковое представление ресурса."""
        return f"{self.content_type}#{self.object_id}"


class ACLEntry(models.Model):
    """
    Модель ACL записей для тонкой настройки прав доступа.

    Позволяет назначать специальные права конкретным пользователям или ролям
    на определенные ресурсы, переопределяя стандартные ролевые права.

    Attributes:
        PRINCIPAL_USER (str): Константа для типа principal - пользователь
        PRINCIPAL_ROLE (str): Константа для типа principal - роль

        resource (ForeignKey): Ресурс, к которому предоставляется доступ
        principal_type (CharField): Тип principal (user или role)
        principal_id (PositiveIntegerField): ID пользователя или роли
        can_read (BooleanField): Разрешение на чтение
        can_update (BooleanField): Разрешение на обновление
        can_delete (BooleanField): Разрешение на удаление
        is_inheritable (BooleanField): Флаг наследуемости прав
        created_at (DateTimeField): Время создания записи
        expires_at (DateTimeField): Время истечения срока действия
    """

    PRINCIPAL_USER = 'user'
    PRINCIPAL_ROLE = 'role'
    PRINCIPAL_CHOICES = [
        (PRINCIPAL_USER, 'User'),
        (PRINCIPAL_ROLE, 'Role'),
    ]

    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='acl_entries',
        verbose_name="Ресурс",
        help_text="Ресурс, к которому предоставляется доступ"
    )
    principal_type = models.CharField(
        max_length=10,
        choices=PRINCIPAL_CHOICES,
        verbose_name="Тип principal",
        help_text="Тип сущности, для которой назначаются права (user или role)"
    )
    principal_id = models.PositiveIntegerField(
        verbose_name="ID principal",
        help_text="ID пользователя или роли, для которой назначаются права"
    )

    # Базовые права
    can_read = models.BooleanField(
        default=False,
        verbose_name="Чтение",
        help_text="Разрешает чтение этого конкретного ресурса"
    )
    can_update = models.BooleanField(
        default=False,
        verbose_name="Обновление",
        help_text="Разрешает обновление этого конкретного ресурса"
    )
    can_delete = models.BooleanField(
        default=False,
        verbose_name="Удаление",
        help_text="Разрешает удаление этого конкретного ресурса"
    )

    # Дополнительные флаги
    is_inheritable = models.BooleanField(
        default=True,
        verbose_name="Наследуется",
        help_text="Определяет, наследуются ли права дочерними ресурсами"
    )

    # Временные метки
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name="Дата создания",
        help_text="Дата и время создания ACL записи"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Срок действия",
        help_text="Дата и время истечения срока действия ACL записи"
    )

    class Meta:
        db_table = 'acl_entries'
        verbose_name = 'ACL запись'
        verbose_name_plural = 'ACL записи'
        indexes = [
            models.Index(fields=['resource', 'principal_type', 'principal_id']),
            models.Index(fields=['expires_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        """Строковое представление ACL записи."""
        principal_type = dict(self.PRINCIPAL_CHOICES).get(self.principal_type, self.principal_type)
        return f"ACL {self.resource} -> {principal_type}#{self.principal_id}"

    def is_active(self):
        """
        Проверяет активность ACL записи.

        Returns:
            bool: True если запись активна (не истек срок действия), иначе False
        """
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def get_principal(self):
        """
        Возвращает объект principal на основе типа и ID.

        Returns:
            User or Role or None: Объект principal или None если не найден
        """
        if self.principal_type == self.PRINCIPAL_USER:
            try:
                return User.objects.get(id=self.principal_id)
            except User.DoesNotExist:
                return None
        elif self.principal_type == self.PRINCIPAL_ROLE:
            try:
                return Role.objects.get(id=self.principal_id)
            except Role.DoesNotExist:
                return None
        return None


@receiver(post_save, sender=User)
def set_default_role(sender, instance, created, **kwargs):
    """
    Сигнал для назначения роли по умолчанию при создании пользователя.

    Автоматически назначает роль 'user' новым пользователям,
    если у них нет других назначенных ролей.

    Args:
        sender: Модель, отправившая сигнал
        instance (User): Созданный пользователь
        created (bool): Флаг создания нового объекта
        **kwargs: Дополнительные аргументы
    """
    if created and not instance.user_roles.exists():
        default_role, _ = Role.objects.get_or_create(
            name='user',
            defaults={'description': 'Обычный пользователь'}
        )
        # Используем get_or_create чтобы избежать дублирования
        UserRole.objects.get_or_create(
            user=instance,
            role=default_role,
            defaults={'assigned_by': instance}
        )