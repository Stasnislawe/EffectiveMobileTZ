import jwt
from django.conf import settings
from django.utils import timezone
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from .models import UserSession, RevokedToken


class CustomJWTAuthentication(authentication.BaseAuthentication):
    """
    Аутентификация по JWT токену
    """

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        # Пропускаем запросы без токена
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header[7:]  # Обрезаем 'Bearer '

        try:
            # Проверяем отозван ли токен
            if self._is_token_revoked(token):
                raise AuthenticationFailed('Token revoked')

            # Декодируем JWT токен
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            session_id = payload.get('session_id')

            if not session_id:
                raise AuthenticationFailed('Invalid token: no session_id')

            # Ищем активную сессию
            session = UserSession.objects.select_related('user').prefetch_related(
                'user__user_roles__role'
            ).get(
                id=session_id,
                is_active=True,
                expires_at__gt=timezone.now(),
                user__is_active=True
            )

            # Обновляем время активности
            session.save()

            return (session.user, token)

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        except UserSession.DoesNotExist:
            raise AuthenticationFailed('Session not found or inactive')

    def _is_token_revoked(self, token):
        """Проверяет наличие токена в blacklist"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'], options={"verify_exp": False})
            jti = payload.get('jti')
            if jti and RevokedToken.objects.filter(jti=jti, expires_at__gt=timezone.now()).exists():
                return True
        except jwt.InvalidTokenError:
            pass
        return False

    def authenticate_header(self, request):
        return 'Bearer realm="api"'