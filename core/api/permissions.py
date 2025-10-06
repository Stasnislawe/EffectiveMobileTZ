from rest_framework import permissions
from .models import AccessRoleRule
from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed


class CustomIsAuthenticated(permissions.BasePermission):
    """
    Permission класс, который возвращает 401 для неаутентифицированных пользователей
    вместо стандартного 403 от DRF.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise AuthenticationFailed(
                'Authentication credentials were not provided.',
                code=401
            )
        return True


class HasPermission(permissions.BasePermission):
    """
    Кастомный permission класс для проверки прав доступа
    """

    def has_permission(self, request, view):
        # Проверка аутентификации (выполняется DRF)
        if not request.user.is_authenticated:
            return False

        # Определяем ресурс и действие из view
        resource_name = getattr(view, 'resource_name', None)
        if not resource_name:
            # Пытаемся определить автоматически
            if hasattr(view, 'queryset') and view.queryset is not None:
                resource_name = view.queryset.model._meta.model_name
            else:
                return False

        action = self._get_action_from_method(request.method)

        # Проверяем права для всех ролей пользователя
        user_roles = request.user.user_roles.select_related('role').all()

        for user_role in user_roles:
            try:
                rule = AccessRoleRule.objects.select_related('element').get(
                    role=user_role.role,
                    element__name=resource_name
                )

                # Проверяем глобальные права
                if rule.has_global_permission(action):
                    return True

                # Проверяем права на свои объекты
                if rule.has_own_permission(action):
                    request.must_filter_by_owner = True
                    return True

            except AccessRoleRule.DoesNotExist:
                continue

        return False

    def _get_action_from_method(self, method):
        """Преобразует HTTP метод в действие"""
        method_map = {
            'GET': 'read',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }
        return method_map.get(method, 'read')

    def has_object_permission(self, request, view, obj):
        """Проверка прав доступа к конкретному объекту"""
        resource_name = getattr(view, 'resource_name', None)
        if not resource_name:
            resource_name = obj._meta.model_name

        action = self._get_action_from_method(request.method)

        user_roles = request.user.user_roles.select_related('role').all()

        for user_role in user_roles:
            try:
                rule = AccessRoleRule.objects.get(
                    role=user_role.role,
                    element__name=resource_name
                )

                # Глобальные права
                if rule.has_global_permission(action):
                    return True

                # Права на свои объекты + проверка владения
                if rule.has_own_permission(action) and self._is_owner(request.user, obj):
                    return True

            except AccessRoleRule.DoesNotExist:
                continue

        return False

    def _is_owner(self, user, obj):
        """Проверяет, является ли пользователь владельцем объекта"""
        if hasattr(obj, 'owner') and obj.owner == user:
            return True
        if hasattr(obj, 'user') and obj.user == user:
            return True
        if hasattr(obj, 'created_by') and obj.created_by == user:
            return True
        return False


class IsAdminUser(permissions.BasePermission):
    """Проверяет, является ли пользователь администратором"""

    def has_permission(self, request, view):
        return (request.user and
                request.user.is_authenticated and
                request.user.user_roles.filter(role__name='admin').exists())