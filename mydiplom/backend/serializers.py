from django.contrib.auth.models import User
from rest_framework import serializers
from backend.models import Category, Product, Shop, Order, OrderItem, ProductInfo, Contact


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class ShopSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Shop
        fields = ('id', 'name', 'user')


class CategorySerializer(serializers.ModelSerializer):
    shops = ShopSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'shops')


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()

    class Meta:
        model = Product
        fields = ('id', 'name', 'category')


class ProductInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInfo
        fields = ('id', 'model', 'price', 'price_rrc')


class OrderItemSerializer(serializers.ModelSerializer):
    shop = ShopSerializer()
    product_info = ProductInfoSerializer()

    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity', 'shop')


class OrderSerializer(serializers.ModelSerializer):
    ordered_items = serializers.SerializerMethodField()
    user = UserSerializer()

    class Meta:
        model = Order
        fields = ('user', 'status', 'ordered_items')

    def get_ordered_items(self, obj):
        order_items = OrderItem.objects.filter(order=obj)
        return OrderItemSerializer(order_items, many=True).data


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('type', 'value')