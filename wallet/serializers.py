from rest_framework import serializers

from auths.models import CustomUser as User 
from .models import Wallet, Transaction

class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta: 
        model = User
        fields = ['id', 'email']
        

class WalletSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    class Meta:
        model = Wallet
        fields = ['user', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['user', 'balance', 'created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['wallet', 'amount', 'transaction_type', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']
        
    
