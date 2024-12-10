from django.db import models
from django.contrib.auth.models import AbstractUser, User

statuses_order = (
    ('cart', 'Корзина'),
    ('confirmed', 'Подтвержден'),
    ('canceled', 'Отменен'),
)


class Shop(models.Model):
    class Meta:
        db_table = 'shop'
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'

    name = models.CharField(max_length=255, verbose_name='Название', null=False, blank=True)
    user = models.OneToOneField(User, verbose_name='Пользователь', blank=True, null=True, on_delete=models.CASCADE)
    url = models.URLField(verbose_name='Ссылка')

    def __str__(self):
        return f'{self.name}'


class Category(models.Model):
    class Meta:
        db_table = 'category'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('name',)

    name = models.CharField(max_length=255, verbose_name='Название', null=False, unique=True)
    shops = models.ManyToManyField(Shop, verbose_name='Магазины', related_name='categories', blank=True)

    def __str__(self):
        return f'{self.name}'


class Product(models.Model):
    class Meta:
        db_table = 'product'
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)

    name = models.CharField(max_length=255, verbose_name='Название', null=False, unique=True)
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='products', null=True, blank=True,
                                 on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name}'


class ProductInfo(models.Model):
    class Meta:
        db_table = 'product_info'
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Информационный список о продуктах'
        ordering = ('name',)

    model = models.CharField(max_length=80, verbose_name='Модель', blank=True)
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='product_infos', null=True, blank=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='product_infos', null=True, blank=True,
                             on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name='Название', null=False, blank=True)
    quantity = models.PositiveIntegerField(verbose_name='Количество', null=False, blank=True)
    price = models.PositiveIntegerField(verbose_name='Цена', null=False, blank=True)
    price_rrc = models.PositiveIntegerField(verbose_name='Рекомендуемая розничная цена', null=False, blank=True)
    external_id = models.PositiveIntegerField(verbose_name='Внешний ID', default=0)

    def __str__(self):
        return f'{self.name}'


class Parameter(models.Model):
    class Meta:
        db_table = 'parameter'
        verbose_name = 'Имя параметра'
        verbose_name_plural = 'Список имен параметров'
        ordering = ('name',)

    name = models.CharField(max_length=255, verbose_name='Название', null=False, unique=True)

    def __str__(self):
        return f'{self.name}'


class ProductParameter(models.Model):
    class Meta:
        db_table = 'product_parameter'
        verbose_name = 'Параметр'
        verbose_name_plural = 'Список параметров'
        ordering = ('id',)

    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте',
                                     related_name='product_parameters', null=True, blank=True, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр', related_name='product_parameters', null=True,
                                  blank=True, on_delete=models.CASCADE)
    value = models.CharField(verbose_name='Значение', max_length=100, null=False, blank=True)

    def __str__(self):
        return f'{self.value}'


class Order(models.Model):
    class Meta:
        db_table = 'order'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Список заказ'
        ordering = ('dt',)

    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(verbose_name='Статус', max_length=25, null=False, blank=True, choices=statuses_order)
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='orders', null=True, blank=True,
                             on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.dt}'


class OrderItem(models.Model):
    class Meta:
        db_table = 'order_item'
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = 'Список заказанных позиций'

    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='ordered_items', null=True, blank=True,
                              on_delete=models.CASCADE)
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте', related_name='ordered_items',
                                     null=True, blank=True, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='ordered_items', null=True, blank=True,
                             on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество', null=False, blank=True)

    def __str__(self):
        return f'{self.order} {self.product_info}'


class Contact(models.Model):
    class Meta:
        db_table = 'contact'
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = 'Список контактов пользователя'

    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='contacts', null=True, blank=True,
                             on_delete=models.CASCADE)
    type = models.CharField(verbose_name='Тип контакта', max_length=255, null=False, blank=True)
    value = models.CharField(verbose_name='Значение', max_length=255, null=False, blank=True)
