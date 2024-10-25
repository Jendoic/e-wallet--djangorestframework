from decimal import Decimal
import requests
import json
import hmac
import hashlib

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.views import APIView

from django.conf import settings
from django.db import transaction as db_transaction
from django.utils.dateparse import parse_date

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from auths.models import CustomUser as User
from .models import Wallet, Transaction
from .serializers import WalletSerializer, TransactionSerializer
from .task import send_notification_email

class WalletViewSet(viewsets.ModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    
    # def get_queryset(self):
    #     return Wallet.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        try:
            wallet = Wallet.objects.get(user=request.user)
            serializer = WalletSerializer(wallet)
            return Response(serializer.data)
        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)

class DepositView(APIView):
    def post(self,  request):   
        user = request.user
        amount = request.data.get('amount')
        
        if not amount:
            return Response({"error": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        wallet = Wallet.objects.get(user=user)
        
        transaction = Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='deposit',
            status='pending',
        )
        
        url = "https://api.paystack.co/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "email": user.email,
            "amount": int(amount) * 100,
            "reference": transaction.reference,
            "callback_url": "https://9668-102-89-22-174.ngrok-free.app/api/v1/verify_deposit"
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code != 200:
            return Response({"error": "Error connecting to Paystack"}, status=response.status_code)
        
        paystack_data = response.json()
        transaction.paystack_reference = paystack_data['data']['reference']
        transaction.save()
        
        return Response({
            "authorization_url": paystack_data['data']['authorization_url'],
            "reference": paystack_data['data']['reference']
        }, status=status.HTTP_200_OK)
        


class PaystackWebhookView(APIView):
    def post(self, request, *args, **kwargs):
     
        signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE', '')
        paystack_data = json.loads(request.body.decode('utf-8'))
        computed_signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            msg=request.body,
            digestmod=hashlib.sha512
        ).hexdigest()

        if signature != computed_signature:
            return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

    
        event = paystack_data['event']
        if event == 'charge.success':
            reference = paystack_data['data']['reference']

            try:
             
                transaction = Transaction.objects.get(reference=reference)

                if transaction.status == 'completed':
                    return Response({'message': 'Transaction already processed'}, status=status.HTTP_200_OK)

              
                transaction.status = 'completed'
                transaction.save()

     
                wallet = transaction.wallet
                wallet.balance += transaction.amount
                wallet.save()
                
                send_notification_email.delay(subject="Transaction Successful",
                                            message=f"Your account has been credited with {transaction.amount}, your account balance is {wallet.balance}",
                                            recipient_list=[wallet.user.email]
                                            )
                
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                'notifications',  
                {
                    'type': 'send_notification',
                    'message': f"Your account has been credited with {transaction.amount}, your account balance is {wallet.balance}",
                }
            )

                return Response({'message': 'Payment verified and wallet updated successfully'}, status=status.HTTP_200_OK)

            except Transaction.DoesNotExist:
                return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'error': 'Unhandled event'}, status=status.HTTP_400_BAD_REQUEST)


class WithdrawView(APIView):
    def post(self, request):
        user = request.user
        amount = request.data.get('amount')
        
        if not amount:
            return Response({"error": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = Decimal(amount)  
        except:
            return Response({"error": "Invalid amount format"}, status=status.HTTP_400_BAD_REQUEST)
        
        if amount <= 0:
            return Response({'error': 'Invalid withdrawal amount'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            wallet = Wallet.objects.get(user=user)
        except Wallet.DoesNotExist:
            return Response({'error': 'Wallet not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if wallet.user != request.user:
            return Response({'error': 'You are not the owner of this wallet'}, status=status.HTTP_401_UNAUTHORIZED)
        
        
        if amount > wallet.balance:
            return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
        
        with db_transaction.atomic():
            transaction = Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type='withdraw',
                status='pending',
            )
            
        # headers = {
        #     "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        #     "Content-Type": "application/json"
        # }
        # data = {
        #     "amount": int(float(amount) * 100), 
        #     "email": user.email, 
        #     "type": "transfer"  
        # }
        
        # paystack_response = requests.post('https://api.paystack.co/transfer', headers=headers, json=data)
        # paystack_data = paystack_response.json()
        
        
        # if paystack_response.status_code != 200:
        #     return Response({"error": paystack_data.get("message", "Failed to initiate withdrawal")}, status=status.HTTP_400_BAD_REQUEST)

        # transaction.paystack_reference = paystack_data['data']['reference']
        # transaction.status = 'completed'  # Update the status to completed
        # transaction.save()

        wallet.balance -= amount
        wallet.save()

        transaction.status = 'completed'
        transaction.save()
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
                'notifications',  
                {
                    'type': 'send_notification',
                    'message': f"You have been debited a sum of {amount}. Your current balance is {wallet.balance}.",
                }
            )
        send_notification_email.delay(subject="Transaction Successful",
                                            message=f"You have been debited a sum of {amount}, your current balance is {wallet.balance}",
                                            recipient_list=[user.email]
                                            )
        return Response({"success": f"Withdrawal of {amount} completed successfully."}, status=status.HTTP_200_OK)
    
        
class TransferView(APIView):
    def post(self, request):
        user = request.user
        amount = request.data.get('amount')
        recipient = request.data.get('recipient')
        
        if not (user and recipient and amount):
            return Response({"error": "All fields (sender_id, recipient, amount) are required."}, status=status.HTTP_400_BAD_REQUEST)
        
       
        
        try:
            amount = Decimal(amount)  
        except:
            return Response({"error": "Invalid amount format"}, status=status.HTTP_400_BAD_REQUEST)
        
      
        
        try:
            sender_wallet = Wallet.objects.get(user=user)
        except Wallet.DoesNotExist:
            return Response({'error': 'Wallet not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            recipient_user = User.objects.get(email=recipient)
            recipient_wallet = Wallet.objects.get(user=recipient_user)
        except User.DoesNotExist:
            return Response({"error": "Recipient not found"}, status=status.HTTP_404_NOT_FOUND)
        except Wallet.DoesNotExist:
            return Response({"error": "Recipient's wallet not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if sender_wallet.user == recipient_wallet.user:
            return Response({"error": "You cannot transfer to yourself"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        if sender_wallet.balance < amount:
            return Response({"error": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with db_transaction.atomic():
                sender_wallet.balance -= amount
                sender_wallet.save()
                
                
                recipient_wallet.balance += amount
                recipient_wallet.save()
                
                
                transaction = Transaction.objects.create(
                    wallet=sender_wallet,
                    amount=amount,
                    transaction_type='transfer',
                    status='completed',
                )
                
            
                transaction = Transaction.objects.create(
                    wallet=recipient_wallet,
                    amount=amount,
                    transaction_type='transfer',
                    status='completed',
                )
                
                send_notification_email.delay(subject="Transaction Successful",
                                            message=f"Your transaction was successful.",
                                            recipient_list=[user.email]
                                            )
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                'notifications',  
                {
                    'type': 'send_notification',
                    'message': f"Your transaction was successful.",
                }
            )
                return Response({"message": "Transfer completed sucessfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class TransactionHistoryView(APIView):
    def get(self, request):
        user = request.user
        wallet = user.wallet

   
        transaction_type = request.query_params.get('transaction_type', None)
        status_filter = request.query_params.get('status', None)
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)


        transactions = Transaction.objects.filter(wallet=wallet)

        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        if status_filter:
            transactions = transactions.filter(status=status_filter)

        if start_date:
            transactions = transactions.filter(created_at__gte=parse_date(start_date))
        
        if end_date:
            transactions = transactions.filter(created_at__lte=parse_date(end_date))


        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)