from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, UserRole, Role, BusinessElement, AccessRoleRule


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 'middle_name']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Неверный email или пароль")

        if not user.is_active:
            raise serializers.ValidationError("Аккаунт деактивирован")

        if not user.check_password(password):
            raise serializers.ValidationError("Неверный email или пароль")

        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'middle_name', 'role', 'roles', 'created_at']
        read_only_fields = ['id', 'email', 'role', 'roles', 'created_at']

    def get_role(self, obj):
        """Возвращает первую роль пользователя (для обратной совместимости)"""
        user_role = obj.user_roles.first()
        return user_role.role.name if user_role else None

    def get_roles(self, obj):
        """Возвращает все роли пользователя"""
        return [user_role.role.name for user_role in obj.user_roles.all()]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'middle_name']


class AccessRoleRuleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    element_name = serializers.CharField(source='element.name', read_only=True)

    class Meta:
        model = AccessRoleRule
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class BusinessElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessElement
        fields = '__all__'


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'