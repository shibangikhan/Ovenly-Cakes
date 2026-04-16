from django.urls import path

from .views import (
    add_to_cart_api,
    api_cart_view,
    api_checkout,
    category_detail_view,
    index_view,
    login_view,
    logout_view,
    order_list_api,
    payment_callback,
    register_view,
    update_cart_item_api,
    remove_cart_item_api,
)

urlpatterns = [
    path('', index_view, name='index'),
    path('category/<int:category_id>/', category_detail_view, name='category_detail'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),

    # API endpoints
    path('api/cart/add/', add_to_cart_api, name='api_add_to_cart'),
    path('api/cart/', api_cart_view, name='api_cart_view'),
    path('api/cart/update/', update_cart_item_api, name='api_update_cart_item'),
    path('api/cart/remove/', remove_cart_item_api, name='api_remove_cart_item'),
    path('api/checkout/', api_checkout, name='api_checkout'),
    path('api/orders/', order_list_api, name='api_orders'),
    path('api/payment/callback/', payment_callback, name='api_payment_callback'),
]
