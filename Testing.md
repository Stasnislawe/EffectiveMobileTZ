Тестирование (проводилось через Postman)
# 🚀 API Documentation - Система управления доступом

## 🔐 Аутентификация

<h3 align="center">Базовые операции управления пользователями</h3>

### 1. 📝 Регистрация пользователя
<p><code>POST</code> <code>http://localhost:8000/api/auth/register/</code></p>

```json
{
    "email": "newuser@example.com",
    "password": "Password123!",
    "password_confirm": "Password123!",
    "first_name": "Иван",
    "last_name": "Петров",
    "middle_name": "Сергеевич"
}
```
2. 🔑 Вход в систему
<p><code>POST</code> <code>http://localhost:8000/api/auth/login/</code></p>

```json

{
    "email": "admin@company.com",
    "password": "Admin123!"
}
```
📤 Ответ:

```json

{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "email": "admin@company.com",
        "first_name": "Алексей",
        "last_name": "Петров",
        "role": "admin"
    }
}
```
3. 👤 Получение профиля
<p><code>GET</code> <code>http://localhost:8000/api/auth/profile/</code></p>

```json
📋 Headers:
Authorization: Bearer <your_token>
```
4. ✏️ Обновление профиля
<p><code>PUT</code> <code>http://localhost:8000/api/auth/profile/</code></p>

```json

📋 Headers:
Authorization: Bearer <your_token>
```
Content-Type: application/json
📦 Body:

```json
{
    "first_name": "НовоеИмя",
    "last_name": "НоваяФамилия",
    "middle_name": "НовоеОтчество"
}
```
5. 🚪 Выход из системы
<p><code>POST</code> <code>http://localhost:8000/api/auth/logout/</code></p>

```json
📋 Headers:

text
Authorization: Bearer <your_token>
```
6. 🗑️ Удаление аккаунта (мягкое)
<p><code>DELETE</code> <code>http://localhost:8000/api/auth/profile/</code></p>

```json
📋 Headers:

Authorization: Bearer <your_token>

```

👑 Административные endpoints
<h3 align="center">Доступно только для пользователей с ролью <code>admin</code></h3>
7. 📋 Получить все правила доступа
<p><code>GET</code> <code>http://localhost:8000/api/admin/access-rules/</code></p>

```json


📋 Headers:
Authorization: Bearer <admin_token>
```
8. ➕ Создать новое правило доступа
<p><code>POST</code> <code>http://localhost:8000/api/admin/access-rules/</code></p>

```json

📋 Headers:
Authorization: Bearer <admin_token>
Content-Type: application/json
```
📦 Body:

```json
{
    "role": 2,
    "element": 3,
    "read_all_permission": true,
    "create_permission": true,
    "update_all_permission": false,
    "delete_all_permission": false,
    "read_own_permission": false,
    "update_own_permission": true,
    "delete_own_permission": true
}
```
9. 🏷️ Получить бизнес-элементы
<p><code>GET</code> <code>http://localhost:8000/api/admin/business-elements/</code></p>

```json

📋 Headers:

text
Authorization: Bearer <admin_token>
```
10. 👥 Получить пользователей с ролями
<p><code>GET</code> <code>http://localhost:8000/api/admin/user-roles/</code></p>

```json

📋 Headers:

Authorization: Bearer <admin_token>
```
11. 🎯 Назначить роль пользователю
<p><code>POST</code> <code>http://localhost:8000/api/admin/user-roles/</code></p>

```json

📋 Headers:

Authorization: Bearer <admin_token>
Content-Type: application/json
```


📦 Body:

```json
{
    "user_id": 3,
    "role_name": "manager"
}
```
12. 📊 Получить все роли
<p><code>GET</code> <code>http://localhost:8000/api/admin/roles/</code></p>

```json

📋 Headers:

Authorization: Bearer <admin_token>
```
📦 Mock бизнес-объекты
<h3 align="center">Демонстрационные endpoints для тестирования системы прав доступа</h3>
13. 🛍️ Получить товары (разные права доступа)
<p><code>GET</code> <code>http://localhost:8000/api/products/</code></p>

```json

📋 Headers:
Authorization: Bearer <your_token>
```
14. 🆕 Создать товар
<p><code>POST</code> <code>http://localhost:8000/api/products/</code></p>

```json

📋 Headers:

Authorization: Bearer <your_token>
Content-Type: application/json
```


📦 Body:

```json

{
    "name": "Новый товар",
    "price": 15000,
    "description": "Описание нового товара"
}
```
15. 📦 Получить заказы
<p><code>GET</code> <code>http://localhost:8000/api/orders/</code></p>

```json

📋 Headers:

Authorization: Bearer <your_token>
```
16. 👥 Получить пользователей (только для admin/manager)
<p><code>GET</code> <code>http://localhost:8000/api/users/</code></p>

```json

📋 Headers:

Authorization: Bearer <admin_token>

```
🎯 Тестовые пользователи для демонстрации
<h3 align="center">Используйте эти учетные данные для тестирования разных ролей</h3>
👑 Администратор (полный доступ)

```json
{
    "email": "admin@company.com",
    "password": "Admin123!"
}
```

💼 Менеджер (расширенные права)

```json
{
    "email": "manager@company.com", 
    "password": "Manager123!"
}
```


👤 Обычный пользователь (ограниченные права)
```json
{
    "email": "user1@company.com",
    "password": "User123!"
}
```
🔄 Последовательность тестирования
<h3 align="center">Рекомендуемые сценарии для проверки функциональности</h3>
🧪 Сценарий 1: Полный цикл нового пользователя
<p><strong>1.</strong> 📝 Регистрация → <code>POST /api/auth/register/</code></p> <p><strong>2.</strong> 🔑 Логин → <code>POST /api/auth/login/</code> (сохранить токен)</p> <p><strong>3.</strong> 👤 Профиль → <code>GET /api/auth/profile/</code></p> <p><strong>4.</strong> 🛍️ Товары → <code>GET /api/products/</code> (должен видеть только свои)</p> <p><strong>5.</strong> 👥 Пользователи → <code>GET /api/users/</code> (должен получить <code>403</code>)</p>
🧪 Сценарий 2: Администратор
<p><strong>1.</strong> 🔑 Логин админа → <code>POST /api/auth/login/</code></p> <p><strong>2.</strong> 👥 Все пользователи → <code>GET /api/users/</code> (должен увидеть всех)</p> <p><strong>3.</strong> 📋 Правила доступа → <code>GET /api/admin/access-rules/</code></p> <p><strong>4.</strong> 🎯 Управление ролями → <code>GET /api/admin/user-roles/</code></p>
🧪 Сценарий 3: Проверка ошибок
<p><strong>1.</strong> ❌ Запрос без токена → <code>GET /api/products/</code> (должен получить <code>401</code>)</p> <p><strong>2.</strong> ❌ Неверный токен → <code>GET /api/products/</code> с неверным токеном (должен получить <code>401</code>)</p>
