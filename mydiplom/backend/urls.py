from django.urls import path

from backend.views import UserRegistration, PartnerUpdate, UserAuthorization, Products, OrderView, ContactView


urlpatterns = [
    path('auth', UserAuthorization.as_view(), name='authorization'),
    path('register', UserRegistration.as_view(), name='user-register'),
    path('upload', PartnerUpdate.as_view(), name='partner-update'),
    path('products', Products.as_view({'get': 'list'}), name='products'),
    path('products/<int:pk>', Products.as_view({'get': 'one_product'}), name='product_one'),
    path('order/cart', OrderView.as_view({'get': 'show_cart'}), name='order-cart'),
    path('order/cart/confirm', OrderView.as_view({'post': 'confirm_cart'}), name='order-cart-confirm'),
    path('order', OrderView.as_view({'get': 'list'}), name='order-list'),
    path('order/add', OrderView.as_view({'post': 'add_products'}), name='add-products'),
    path('order/cart/delete', OrderView.as_view({'post': 'delete_products'}), name='delete-products'),
    path('contacts/list', ContactView.as_view({'get': 'list'}), name='contact-list'),
    path('contacts/create', ContactView.as_view({'post': 'create'}), name='contact-create'),
    path('contacts/delete', ContactView.as_view({'delete': 'delete_contact'}), name='contact-delete'),
]