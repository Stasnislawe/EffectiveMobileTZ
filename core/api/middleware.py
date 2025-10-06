import jwt
from django.conf import settings
from django.utils import timezone
from .models import UserSession, RevokedToken


class CustomAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Исключаем админку Django и публичные пути
        if request.path.startswith('/admin/') or request.path in [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/docs/',
            '/api/schema/'
        ]:
            return self.get_response(request)

        auth_header = request.headers.get('Authorization')
        token = None

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]

        # Инициализируем пользователя как None
        request.user = None

        if token:
            try:
                # Проверяем базовый формат
                if token.count('.') == 2:
                    # Проверяем blacklist
                    if not self._is_token_revoked(token):
                        # Декодируем JWT токен
                        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                        session_id = payload.get('session_id')

                        if session_id:
                            # Ищем активную сессию
                            session = UserSession.objects.select_related('user').prefetch_related(
                                'user__user_roles__role'
                            ).get(
                                id=session_id,
                                is_active=True,
                                expires_at__gt=timezone.now(),
                                user__is_active=True
                            )

                            # Устанавливаем пользователя
                            request.user = session.user

                            # Обновляем время активности
                            session.save()
                else:
                    print(f"Invalid token format: {token}")

            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, UserSession.DoesNotExist) as e:
                print(f"Middleware auth error: {e}")
                # Продолжаем без пользователя

        response = self.get_response(request)
        return response

    def _is_token_revoked(self, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'], options={"verify_exp": False})
            jti = payload.get('jti')
            if jti and RevokedToken.objects.filter(jti=jti, expires_at__gt=timezone.now()).exists():
                return True
        except jwt.InvalidTokenError:
            pass
        return False