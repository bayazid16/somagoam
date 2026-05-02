from django.shortcuts import render
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from .serializers import UserProfileSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

class UserProfileView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        
        return self.request.user
    




def get_tokens(user):
    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }






@csrf_exempt
def facebook_data_deletion(request):
    if request.method == 'POST':
        return JsonResponse({
            "url": "https://somagoam.com/data-deletion-status",
            "confirmation_code": "somagoam_data_deleted"
        })
    return JsonResponse({"status": "ok"})

# Create your views here.
