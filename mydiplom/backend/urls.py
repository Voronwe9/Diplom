

from django.urls import path

from backend.views import UserRegistration, PartnerUpdate, UserAuthorization, Products, OrderView

urlpatterns = [
    path('auth', UserAuthorization.as_view(), name='authorization'),
    path('register', UserRegistration.as_view(), name='user-register'),
    path('upload', PartnerUpdate.as_view(), name='partner-update'),
    path('products', Products.as_view({'get': 'list'}), name='products'),
    path('products/<int:pk>', Products.as_view({'get': 'one_product'}), name='product_one'),
    path('order', OrderView.as_view({'get': 'list'}), name='order'),
    path('order/add', OrderView.as_view({'post': 'add_products'}), name='add_products'),



]