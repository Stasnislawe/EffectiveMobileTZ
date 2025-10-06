from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..permissions import HasPermission, CustomIsAuthenticated
from ..models import User


class MockProductView(APIView):
    """
    Mock API для товаров
    Минимальные объекты бизнес-приложения
    """
    permission_classes = [CustomIsAuthenticated, HasPermission]
    resource_name = 'products'

    def get(self, request):
        # Имитация данных товаров - только один продукт принадлежит текущему пользователю
        mock_products = [
            {"id": 1, "name": "Ноутбук", "price": 50000, "owner_id": 999},  # Чужой продукт
            {"id": 2, "name": "Смартфон", "price": 30000, "owner_id": 998},  # Чужой продукт
            {"id": 3, "name": "Планшет", "price": 25000, "owner_id": request.user.id},  # Продукт текущего пользователя
        ]

        # Фильтрация по владельцу если нужно
        if getattr(request, 'must_filter_by_owner', False):
            # Оставляем только продукты текущего пользователя
            mock_products = [p for p in mock_products if p['owner_id'] == request.user.id]

        return Response(mock_products)

    def post(self, request):
        # Mock создание товара
        if getattr(request, 'must_filter_by_owner', False):
            pass

        return Response(
            {"message": "Товар создан", "data": request.data},
            status=status.HTTP_201_CREATED
        )


class MockOrderView(APIView):
    permission_classes = [CustomIsAuthenticated, HasPermission]
    resource_name = 'orders'

    def get(self, request):
        mock_orders = [
            {"id": 1, "product": "Ноутбук", "status": "доставляется", "owner_id": 999},
            {"id": 2, "product": "Смартфон", "status": "обработка", "owner_id": 998},
            {"id": 3, "product": "Планшет", "status": "выполнен", "owner_id": request.user.id},
        ]

        if getattr(request, 'must_filter_by_owner', False):
            mock_orders = [o for o in mock_orders if o['owner_id'] == request.user.id]

        return Response(mock_orders)


class MockUserManagementView(APIView):
    permission_classes = [HasPermission]
    resource_name = 'users'

    def get(self, request):
        # Только пользователи с глобальными правами увидят всех пользователей
        users = User.objects.filter(is_active=True).values('id', 'email', 'first_name', 'last_name')

        if getattr(request, 'must_filter_by_owner', False):
            # В реальной системе здесь была бы фильтрация
            users = users.filter(id=request.user.id)

        return Response(list(users))