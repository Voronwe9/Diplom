from django.core.handlers.wsgi import WSGIRequest
from django.core.validators import URLValidator
from django.http import JsonResponse
from requests import get
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import yaml
from rest_framework.decorators import action
from backend.serializers import UserSerializer, ProductSerializer, OrderSerializer

from backend.models import Shop, Category, ProductInfo, Product, ProductParameter, Parameter, Order



class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]  # mixin

    def post(self, request: WSGIRequest, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        # if self.request.user.type != 'shop':
        #     return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        url = self.request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content
                data = yaml.safe_load(stream)

                shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=self.request.user.id)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'],
                                                              quantity=item['quantity'],
                                                              shop_id=shop.id)
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)

                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class UserRegistration(APIView):
    def post(self, request, *args, **kwargs):
        serializers = UserSerializer(data=request.data)

        if serializers.is_valid():
            user = serializers.save()
            user.set_password(self.request.data.get('password'))
            user.save()
            return Response({'status': 'OK', 'id': user.id}, status=status.HTTP_201_CREATED)
        return Response({'status': 'ERROR', 'errors': serializers.errors}, status=status.HTTP_400_BAD_REQUEST)


class Products(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    @action(detail = False, methods=['get'], name = 'one_product')
    def one_product(self, request, *args, **kwargs):
        return Response(ProductSerializer(self.queryset.filter(id = kwargs['pk']).first()).data)


class UserAuthorization(APIView):

    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        content = {
            'user': str(request.user),
            'auth': str(request.auth),
        }
        return Response(content, status=status.HTTP_200_OK)
    
class OrderView(ModelViewSet):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]
    
    queryset = Order.objects.get_queryset()
    serializer_class = OrderSerializer

    def get_queryset(self):
        qs = self.queryset.filter(user_id=self.request.user.id)
        return qs
    @action(detail = False, methods=['post'], name = 'add_products')
    def add_products(self, request, *args, **kwargs):
        if len(self.get_queryset()) > 0:
            order = self.get_queryset().first()
            product_info_ids = request.data.get('product_info_ids', [])
            for product_info_id in product_info_ids:
                create_order_item(order, product_info_id)
            return Response({'message': 'Товары добавлены в заказ'})
        return Response({'message': 'Заказ не найден'}, status=404)

    def create_order_item(order, product_info_id):
        OrderItem.objects.create(
            order=order,
            product_info_id=product_info_id,
            shop_id=order.user.shop.id,
            quantity=1
        )