from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIRequest
from django.core.validators import URLValidator
from django.db.models import QuerySet
from django.http import JsonResponse
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
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
from backend.serializers import UserSerializer, ProductSerializer, OrderSerializer, ContactSerializer

from backend.models import Shop, Category, ProductInfo, Product, ProductParameter, Parameter, Order, Contact

from backend.models import OrderItem

from mydiplom import settings


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
            password = get_random_string(length=16)
            user = serializers.save()
            user.set_password(password)
            user.save()
            send_mail(
                "Регистрация",
                f"{user.username}, Вы успешно зарегестрировались на сайте goods.ru!\n"
                f"Ваш username: {user.username}\n"
                f"Ваш пароль: {password}",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False
            )
            return Response({
                'status': 'OK',
                'message': f'Письмо с паролем было отправлено на почту {request.data.get("email")}'
            }, status=status.HTTP_201_CREATED)
        return Response({'status': 'ERROR', 'errors': serializers.errors}, status=status.HTTP_400_BAD_REQUEST)


class Products(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @action(detail=False, methods=['get'], name='one_product')
    def one_product(self, request, *args, **kwargs):
        return Response(ProductSerializer(self.queryset.filter(id=kwargs['pk']).first()).data)


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

    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        qs = self.queryset.filter(user_id=self.request.user.id)
        return qs

    @action(detail=False, methods=['post'], name='confirm_cart')
    def confirm_cart(self, request: WSGIRequest, *args, **kwargs):
        address = request.data.get('address', None)
        if not address:
            return Response({"message": "обязательно укажите поле \"address\" для создания заказа"},
                            status=status.HTTP_400_BAD_REQUEST)
        elif not (address := Contact.objects.filter(user=self.request.user, type=address)).exists():
            return Response({"message": "Указанный Вами адрес не существует"},
                            status=status.HTTP_400_BAD_REQUEST)
        qs: QuerySet = self.get_queryset().filter(status='cart')
        if len(qs) == 0:
            return Response({'message': 'Ваша корзина пуста'}, status=status.HTTP_200_OK)

        orders_text = []

        cart: Order = qs.first()
        cart.status = 'confirmed'
        for oi in cart.ordered_items.all():
            orders_text.append(f"Товар {oi.product_info.name} ({oi.quantity} шт.)")
            oi.product_info.quantity -= oi.quantity
            oi.product_info.save()
        cart.save()

        t = '\n'.join(orders_text)
        send_mail(
            "Подтверждение заказа",
            f"{request.user.username}, Ваш заказ успешно создан!\n"
            f"{t}",
            settings.EMAIL_HOST_USER,
            [request.user.email],
            fail_silently=False
        )

        return Response({'message': 'Ваш заказ успешно создан!'}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], name='delete_products')
    def delete_products(self, request: WSGIRequest, *args, **kwargs):
        qs: QuerySet = self.get_queryset().filter(status='cart')
        if len(qs) == 0:
            return Response({'message': 'Ваша корзина пуста'}, status=status.HTTP_200_OK)
        cart: Order = qs.first()
        order_items: list[dict] = request.data.get('order_items', [])
        for oi in order_items:
            if 'product_id' not in oi.keys() or \
                    'quantity' not in oi.keys():
                return Response({'message': 'Неверный формат входных данных'},
                                status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            cart_item = cart.ordered_items.filter(product_info_id=oi.get('product_id'))
            if len(cart_item) > 0:
                item = cart_item.first()
                item.quantity -= oi.get('quantity', 0)
                if item.quantity <= 0:
                    item.delete()
                else:
                    item.save()
        return Response({'message': f'{len(order_items)} товаров было удалено из корзины'},
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], name='show_cart')
    def show_cart(self, request: WSGIRequest, *args, **kwargs):
        qs: QuerySet = self.get_queryset().filter(status='cart')
        if len(qs) == 0:
            return Response({'message': 'Ваша корзина пуста'}, status=status.HTTP_200_OK)
        return Response(OrderSerializer(qs.first()).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], name='add_products')
    def add_products(self, request: WSGIRequest, *args, **kwargs):
        qs: QuerySet = self.get_queryset()
        if len(qs) == 0 or len(cart := qs.filter(status='cart')) == 0:
            order = Order(
                status='cart',
                user=self.request.user
            )
            order.save()
        else:
            order = cart.first()

        product_infos: list[dict] = request.data.get('product_info_ids', [])
        for product_info in product_infos:
            if 'id' not in product_info.keys() or \
                    'quantity' not in product_info.keys() or \
                    'shop_id' not in product_info.keys():
                return Response({'message': 'Неверный формат входных данных'},
                                status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            OrderItem(
                order=order,
                quantity=product_info.get('quantity', 0),
                product_info_id=product_info.get('id', None),
                shop_id=product_info.get('shop_id', 0),
            ).save()
        return Response({'message': f'{len(product_infos)} товаров было добавлено в корзину'},
                        status=status.HTTP_200_OK)


class ContactView(ModelViewSet):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user_id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        serializer: ContactSerializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['delete'], name='delete_contact')
    def delete_contact(self, request, *args, **kwargs):
        obj = self.get_queryset().filter(
            type=request.data.get('type', 'Неизвестно'),
            value=request.data.get('value', None)
        )
        if obj.exists():
            obj.delete()
            return Response({"message": "Контакт был удален"}, status=status.HTTP_200_OK)
        return Response({"message": "Такого контакта нет"}, status=status.HTTP_404_NOT_FOUND)
