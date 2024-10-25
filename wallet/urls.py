from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WalletViewSet, TransferView, DepositView, WithdrawView, TransactionHistoryView

router = DefaultRouter()
router.register(r'wallet', WalletViewSet, basename='wallet')
# router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
    path('deposit/', DepositView.as_view()),
    path('withdraw/', WithdrawView.as_view()),
    path('transfer/', TransferView.as_view()),
    path('transactions/history/', TransactionHistoryView.as_view()),
   
]
