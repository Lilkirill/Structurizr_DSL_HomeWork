workspace {
    name "Ozon Online Store"
    !identifiers hierarchical

    model {

        
        customer = Person "Customer" 
        seller = Person "Seller" 
        courier = Person "Courier"

        
        payment = softwareSystem "Payment System"
        delivery = softwareSystem "Delivery System"

        
        ozon = softwareSystem "Ozon Online Store" {
            -> payment "Process payment"
            -> delivery "Arrange delivery"

            
            user_service = container "User Service" {
            
                component "User Registration"
                component "User Authentication"
                component "User Profile Management"
                component "User Search by Login"
                component "User Search by Name Mask"
            }

           
            product_service = container "Product Service" {
               
                component "Product Creation"
                component "Product Catalog"
                component "Product Search"
            }

                cart_service = container "Cart Service" {
                    -> product_service "Get product details" "REST"
            }

            
            order_service = container "Order Service" {
                -> cart_service "Get cart details" "REST"
                -> payment "Process payment" "REST"
                -> delivery "Create delivery order" "REST"
            }

            
            recommendation_service = container "Recommendation Service" {

                -> product_service "Get product data" "REST"
            }

            
            courier_service = container "Courier Service" {
                -> order_service "Get delivery details" "REST"
            }
        }


        customer -> ozon.user_service "Register/Login" "REST"
        customer -> ozon.user_service "Search by login/name" "REST"
        customer -> ozon.product_service "Browse products" "REST"
        customer -> ozon.cart_service "Add to cart" "REST"
        customer -> ozon.order_service "Place order" "REST"
        customer -> ozon.recommendation_service "Get recommendations" "REST"

        seller -> ozon.product_service "Create product" "REST"
        seller -> ozon.order_service "Receive payment" "REST"

        courier -> ozon.courier_service "Accept delivery" "REST"
        courier -> ozon.courier_service "Update delivery status" "REST"

        deploymentEnvironment "c4" {
            deploymentNode "DMZ" {
                deploymentNode "web-app.ozon.ru" {
                    containerInstance ozon.user_service
                    containerInstance ozon.product_service
                }
            }

            deploymentNode "PROTECTED" {
                deploymentNode "k8.namespace" {
                    lb = infrastructureNode "LoadBalancer"

                    pod1 = deploymentNode "pod1" {
                        us = containerInstance ozon.user_service
                        instances 5
                    }
                    deploymentNode "pod2" {
                        containerInstance ozon.product_service
                    }
                    deploymentNode "pod3" {
                        containerInstance ozon.cart_service
                        containerInstance ozon.order_service
                    }
                    deploymentNode "pod4" {
                        containerInstance ozon.courier_service
                        containerInstance ozon.recommendation_service
                    }

                    lb -> pod1.us "Send requests"
                }
            }
        }
    }

    views {

        themes default

        systemContext ozon "c1" {
            include *
            # autoLayout lr
        }

        container ozon "c2" {
            include *
            autoLayout
        }

    
        component ozon.user_service "c3" {
            include *
            autoLayout
        }

        deployment * "c4" {
            include *
            autoLayout
        }
    }
}