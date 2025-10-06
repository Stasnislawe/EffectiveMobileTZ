from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import AccessRoleRule, BusinessElement, Role, User, UserRole
from ..serializers import AccessRoleRuleSerializer, BusinessElementSerializer, RoleSerializer
from ..permissions import IsAdminUser


class UserRoleManagementView(APIView):
    """API для управления ролями пользователей"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Получение списка пользователей с их ролями"""
        users = User.objects.filter(is_active=True).prefetch_related('user_roles__role')
        user_data = []

        for user in users:
            user_roles = [ur.role.name for ur in user.user_roles.all()]
            user_data.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'roles': user_roles
            })

        return Response(user_data)

    def post(self, request):
        """Назначение роли пользователю"""
        user_id = request.data.get('user_id')
        role_name = request.data.get('role_name')

        try:
            user = User.objects.get(id=user_id, is_active=True)
            role = Role.objects.get(name=role_name)

            UserRole.objects.get_or_create(user=user, role=role)

            return Response({'message': f'Роль {role_name} назначена пользователю {user.email}'})

        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
        except Role.DoesNotExist:
            return Response({'error': 'Роль не найдена'}, status=status.HTTP_404_NOT_FOUND)


class RoleManagementView(APIView):
    """API для управления ролями"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        roles = Role.objects.all()
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Создание новой роли"""
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccessRoleRuleView(APIView):
    """
    API для управления правилами доступа
    Реализовано API с возможностью получения и изменения этих правил
    пользователю, имеющему роль администратора.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Получение всех правил доступа"""
        rules = AccessRoleRule.objects.select_related('role', 'element').all()
        serializer = AccessRoleRuleSerializer(rules, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Создание нового правила доступа"""
        serializer = AccessRoleRuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccessRoleRuleDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_object(self, pk):
        try:
            return AccessRoleRule.objects.get(pk=pk)
        except AccessRoleRule.DoesNotExist:
            return None

    def get(self, request, pk):
        rule = self.get_object(pk)
        if not rule:
            return Response({"error": "Rule not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = AccessRoleRuleSerializer(rule)
        return Response(serializer.data)

    def put(self, request, pk):
        rule = self.get_object(pk)
        if not rule:
            return Response({"error": "Rule not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = AccessRoleRuleSerializer(rule, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        rule = self.get_object(pk)
        if not rule:
            return Response({"error": "Rule not found"}, status=status.HTTP_404_NOT_FOUND)

        rule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BusinessElementView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        elements = BusinessElement.objects.all()
        serializer = BusinessElementSerializer(elements, many=True)
        return Response(serializer.data)