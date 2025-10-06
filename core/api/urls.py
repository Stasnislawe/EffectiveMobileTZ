from django.urls import path
from .views import auth, admin, mock_views

urlpatterns = [
    # Аутентификация
    path('auth/register/', auth.register, name='register'),
    path('auth/login/', auth.login, name='login'),
    path('auth/logout/', auth.logout, name='logout'),
    path('auth/profile/', auth.UserProfileView.as_view(), name='profile'),

    # Управление правами (админка)
    path('admin/access-rules/', admin.AccessRoleRuleView.as_view(), name='access-rules-list'),
    path('admin/access-rules/<int:pk>/', admin.AccessRoleRuleDetailView.as_view(), name='access-rules-detail'),
    path('admin/business-elements/', admin.BusinessElementView.as_view(), name='business-elements'),
    path('admin/user-roles/', admin.UserRoleManagementView.as_view(), name='user-roles-management'),
    path('admin/roles/', admin.RoleManagementView.as_view(), name='roles-management'),

    # Mock бизнес-объекты
    path('products/', mock_views.MockProductView.as_view(), name='products'),
    path('orders/', mock_views.MockOrderView.as_view(), name='orders'),
    path('users/', mock_views.MockUserManagementView.as_view(), name='users'),
]