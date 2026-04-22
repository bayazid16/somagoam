
from .models import Order
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from .serializers import OrderHistorySerializer






class OrderHistoryListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderHistorySerializer

    def get_queryset(self):

        return Order.objects.filter(user=self.request.user).order_by('-created_at')
