from django.contrib import admin
from django.urls import path, include
from wallet.views import PaystackWebhookView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('auths.urls')),
    path('api/v1/', include('wallet.urls')),
    path('api/v1/paystackWebHook/', PaystackWebhookView.as_view())
]
