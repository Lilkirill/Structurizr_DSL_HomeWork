workspace {
    !identifiers hierarchical
    
    model {
        user = person "Пользователь" "Пользователь магазина"
        admin = person "Администратор" "Управляет сервисами"

        postgres_db = softwareSystem "PostgreSQL" {
            description "Хранит данные"
        }

        ecommerce_system = softwareSystem "Интернет-магазин" {
            description "Магазин для покупки товаров"

            api_gateway = container "API Gateway" {
                description "Вход для сервисов"
                technology "FastAPI + Uvicorn"
            }

            user_service = container "User Service" {
                description "Создание пользователей, аутентификация, доступ к данным"
                technology "Python, FastAPI, SQLAlchemy, PostgreSQL"

                AuthController = component "AuthController" {
                    description "Аутентификации пользователей"
                    technology "FastAPI"
                }
                UserRepository = component "UserRepository" {
                    description "Работает с базой данных"
                    technology "SQLAlchemy"
                }
                AuthController -> UserRepository "Взаимодействие с БД"
            }

            product_service = container "Product Service" {
                description "Взаимодействие товарами"
                technology "Python, FastAPI, SQLAlchemy, PostgreSQL"

                ProductController = component "ProductController" {
                    description "Обрабатывает запросы к товарам"
                    technology "FastAPI"
                }
                ProductRepository = component "ProductRepository" {
                    description "Работает с базой данных"
                    technology "SQLAlchemy"
                }
                ProductController -> ProductRepository "Взаимодействие с БД"
            }

            cart_service = container "Cart Service" {
                description "Сервис корзин пользователей"
                technology "Python, FastAPI, SQLAlchemy, PostgreSQL"

                CartController = component "CartController" {
                    description "Обрабатывает действия с корзиной"
                    technology "FastAPI"
                }
                CartRepository = component "CartRepository" {
                    description "Работает с таблицей cart_items в базе данных"
                    technology "SQLAlchemy"
                }
                CartController -> CartRepository "Взаимодействие с БД"
            }

            user_service -> postgres_db "Чтение/запись users" "JDBC, TCP:5432"
            product_service -> postgres_db "Чтение/запись products" "JDBC, TCP:5432"
            cart_service -> postgres_db "Чтение/запись cart_items" "JDBC, TCP:5432"
        }

        user -> ecommerce_system.api_gateway "HTTP запросы к сервисам"
        admin -> ecommerce_system.api_gateway "HTTP запросы к сервисам"
        ecommerce_system.api_gateway -> ecommerce_system.user_service "REST, HTTPS:8000"
        ecommerce_system.api_gateway -> ecommerce_system.product_service "REST, HTTPS:8001"
        ecommerce_system.api_gateway -> ecommerce_system.cart_service "REST, HTTPS:8002"
    }

    views {
        systemContext ecommerce_system "C1_Context" {
            include *
            autolayout lr
        }

        container ecommerce_system "C2_Container" {
            include *
            autolayout lr
        }

        component ecommerce_system.user_service "C4_UserService_Components" {
            include *
            autolayout lr
        }

        component ecommerce_system.product_service "C4_ProductService_Components" {
            include *
            autolayout lr
        }

        component ecommerce_system.cart_service "C4_CartService_Components" {
            include *
            autolayout lr
        }

       
        dynamic ecommerce_system "UserRegistration" {
            user -> ecommerce_system.api_gateway "POST /users"
            ecommerce_system.api_gateway -> ecommerce_system.user_service "REST"
            ecommerce_system.user_service -> postgres_db "SQL insert"
        }

        dynamic ecommerce_system "UserAuthentication" {
            user -> ecommerce_system.api_gateway "POST /token"
            ecommerce_system.api_gateway -> ecommerce_system.user_service "REST"
            ecommerce_system.user_service -> postgres_db "SQL select"
        }

        dynamic ecommerce_system "AddToCart" {
            user -> ecommerce_system.api_gateway "POST /cart"
            ecommerce_system.api_gateway -> ecommerce_system.cart_service "REST"
            ecommerce_system.cart_service -> postgres_db "SQL insert"
        }

        dynamic ecommerce_system "AddProduct" {
            admin -> ecommerce_system.api_gateway "POST /products"
            ecommerce_system.api_gateway -> ecommerce_system.product_service "REST"
            ecommerce_system.product_service -> postgres_db "SQL insert"
        }

        dynamic ecommerce_system "GetProducts" {
            user -> ecommerce_system.api_gateway "GET /products"
            ecommerce_system.api_gateway -> ecommerce_system.product_service "REST"
            ecommerce_system.product_service -> postgres_db "SQL select"
        }
    }
}