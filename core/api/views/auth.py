from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
import jwt
from django.conf import settings
from django.utils import timezone

from ..models import User, RevokedToken
from ..serializers import UserRegisterSerializer, UserLoginSerializer, UserProfileSerializer, UserUpdateSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Регистрация нового пользователя
    """
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {"message": "Пользователь успешно зарегистрирован"},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Аутентификация пользователя
    """

    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']

        token = user.create_session()

        return Response({
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.user_roles.first().role.name if user.user_roles.first() else None
            }
        })
    else:
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Выход из системы
    """
    # Добавляем токен в blacklist
    token = request.auth
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'], options={"verify_exp": False})
            jti = payload.get('jti')
            exp = payload.get('exp')
            if jti and exp:
                expires_at = timezone.datetime.fromtimestamp(exp, tz=timezone.utc)
                RevokedToken.objects.get_or_create(jti=jti, defaults={'expires_at': expires_at})
        except jwt.InvalidTokenError:
            pass

    # Деактивируем сессии пользователя
    request.user.sessions.filter(is_active=True).update(is_active=False)

    return Response({"message": "Успешный выход из системы"})


class UserProfileView(APIView):
    """
    Управление профилем пользователя
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получение профиля пользователя"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        """Обновление профиля пользователя"""
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            profile_serializer = UserProfileSerializer(request.user)
            return Response(profile_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Мягкое удаление аккаунта"""
        request.user.soft_delete()
        return Response({"message": "Аккаунт успешно удален"})