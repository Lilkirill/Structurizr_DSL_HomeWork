workspace {
    name "Ozon Online Store"
    !identifiers hierarchical

    model {
        // Actors
        customer = person "Customer" "Online shopper"
        seller = person "Seller" "Product vendor"
        courier = person "Courier" "Delivery personnel"
        admin = person "Admin" "System administrator"

        // External systems
        payment = softwareSystem "Payment System" "Processes financial transactions"
        delivery = softwareSystem "Delivery System" "Manages order deliveries"

        // Main system
        ozon = softwareSystem "Ozon Online Store" "E-commerce platform" {
            // Authentication service
            auth_service = container "Auth Service" "Handles JWT authentication" {
                component "Token Generator" "Generates JWT tokens"
                component "Credential Validator" "Validates user credentials"
                component "Master User" "Predefined admin (admin/secret)"
            }

            // Existing services with JWT support
            user_service = container "User Service" "Manages users" {
                component "User Registration" "Handles new user signups"
                component "User Profile Management" "Manages user data"
                component "User Search" "Finds users by login/name"
                component "JWT Validator" "Validates JWT tokens"
            }

            product_service = container "Product Service" "Manages products" {
                component "Product Catalog" "Maintains product listings"
                component "Product Search" "Provides search functionality"
                component "JWT Validator" "Validates JWT tokens"
            }

            cart_service = container "Cart Service" "Manages shopping carts" {
                component "Cart Manager" "Handles cart operations"
                component "JWT Validator" "Validates JWT tokens"
            }

            order_service = container "Order Service" "Processes orders" {
                component "Order Processor" "Handles order lifecycle"
                component "JWT Validator" "Validates JWT tokens"
            }

            // Other services remain unchanged
            recommendation_service = container "Recommendation Service" {
                -> product_service "Get product data" "REST"
            }

            courier_service = container "Courier Service" {
                -> order_service "Get delivery details" "REST"
            }

            // Internal relationships with auth
            auth_service -> user_service "Validates credentials" "HTTP"
            user_service -> auth_service "Gets token info" "HTTP"
            product_service -> auth_service "Validates tokens" "HTTP"
            cart_service -> auth_service "Validates tokens" "HTTP"
            order_service -> auth_service "Validates tokens" "HTTP"
        }

        // User interactions with authentication
        customer -> ozon.auth_service "Get JWT token" "HTTP"
        customer -> ozon.user_service "Manage profile [JWT]" "HTTP"
        customer -> ozon.product_service "Browse products [JWT]" "HTTP"
        customer -> ozon.cart_service "Manage cart [JWT]" "HTTP"
        customer -> ozon.order_service "Place orders [JWT]" "HTTP"
        
        admin -> ozon.auth_service "Get admin token" "HTTP"
        admin -> ozon.user_service "Manage users [JWT]" "HTTP"
        admin -> ozon.product_service "Manage catalog [JWT]" "HTTP"

        // Other interactions remain unchanged
        seller -> ozon.product_service "Create product [JWT]" "HTTP"
        seller -> ozon.order_service "Receive payment [JWT]" "HTTP"
        courier -> ozon.courier_service "Accept delivery [JWT]" "HTTP"
        courier -> ozon.courier_service "Update status [JWT]" "HTTP"

        // Deployment with auth service
        deploymentEnvironment "Production" {
            deploymentNode "DMZ" {
                deploymentNode "web-app.ozon.ru" {
                    containerInstance ozon.auth_service
                    containerInstance ozon.user_service
                }
            }

            deploymentNode "PROTECTED" {
                deploymentNode "k8.namespace" {
                    lb = infrastructureNode "LoadBalancer"

                    pod1 = deploymentNode "auth-pod" {
                        auth = containerInstance ozon.auth_service
                        instances 3
                    }
                    deploymentNode "service-pod" {
                        containerInstance ozon.user_service
                        containerInstance ozon.product_service
                    }
                    deploymentNode "order-pod" {
                        containerInstance ozon.cart_service
                        containerInstance ozon.order_service
                    }
                    deploymentNode "delivery-pod" {
                        containerInstance ozon.courier_service
                        containerInstance ozon.recommendation_service
                    }

                    lb -> pod1.auth "Route auth requests"
                }
            }
        }
    }

  views {
        theme default

        systemContext ozon "SystemContext" {
            include *
            autoLayout
        }

        container ozon "Containers" {
            include *
            autoLayout
        }

        component ozon.auth_service "AuthComponents" {
            include *
            autoLayout
        }

        
        deployment ozon "Production" "ProductionDeployment" {
            include *
            autoLayout
        }
    }
}