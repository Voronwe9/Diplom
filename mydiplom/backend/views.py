from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.serializers import UserSerializer

class UserRegistration(APIView):
    def post(self, request, *args, **kwargs):
        serializers = UserSerializer(data=request.data)

        if serializers.is_valid():
            user = serializers.save()
            return Response({'status': 'OK', 'id': user.id}, status=status.HTTP_201_CREATED)
        return Response({'status': 'ERROR', 'errors': serializers.errors}, status=status.HTTP_400_BAD_REQUEST)

