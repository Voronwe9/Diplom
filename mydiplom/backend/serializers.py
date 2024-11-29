from django.contrib.auth.models import User
from rest_framework import serializers
from backend.models import Category

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        

