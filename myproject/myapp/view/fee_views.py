from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import User, FeeTransaction, Enrollment, Student
from ..serializers import  FeeTransactionSerializer
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

#FOR STUDENT FEE PAYMENT
@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def fee_payment(request):
    if request.method == 'POST':
        try:
            # only admin can process payments
            if request.user.role != 'admin':
                return Response({'error': "Permission denied. Admin access required."}, status=status.HTTP_403_FORBIDDEN)

            # Get Payment Details from Request
            enrollment_id = request.data.get('enrollment_id')
            amount = request.data.get('amount')
            method = request.data.get('method')
            payment_date = request.data.get('payment_date')
            # transaction_id = request.data.get('transaction_id', '')
            remarks = request.data.get('remarks', '')

            # Required fields validation
            if not enrollment_id:
                return Response({'error': "enrollment_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            if not amount:
                return Response({'error': "amount is required"}, status=status.HTTP_400_BAD_REQUEST)

            if not method:
                return Response({'error': "payment_method is required"}, status=status.HTTP_400_BAD_REQUEST)

            # checking if enrollment exists
            try:
                enrollment = Enrollment.objects.get(id=enrollment_id)
            except Enrollment.DoesNotExist:
                return Response({'error': "Enrollment not found"}, status=status.HTTP_404_NOT_FOUND)

            # Validate amount (amount number ho vanera check garxa)
            try:
                amount_float = float(amount)
            except (ValueError, TypeError):
                return Response({'error': "Invalid amount value"}, status=status.HTTP_400_BAD_REQUEST)

            # fee amount course fee vanda dher ta xaina vanera check garne
            fee_amount = float(enrollment.course.fee_amount)
            if amount_float > fee_amount:
                return Response({'error': f"Payment amount {amount_float} exceeds course fee {fee_amount}"}, status=status.HTTP_400_BAD_REQUEST)

            # payment save garne
            payment = FeeTransaction.objects.create(
                enrollment=enrollment,
                amount=amount_float,
                method=method,
                payment_date=payment_date,
                remarks=remarks
            )

            serializer = FeeTransactionSerializer(payment)
            return Response({
                'msg': "Payment processed successfully",'payment': serializer.data}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': "Failed to process payment",'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif request.method == 'GET':
        try:
            if request.user.role == 'student':
                try:
                    student = Student.objects.get(user=request.user)
                    payments = FeeTransaction.objects.filter(enrollment__student=student)
                except Student.DoesNotExist:
                    return Response({'error': "Student profile not found"}, status=status.HTTP_404_NOT_FOUND)

            elif request.user.role == 'admin':
                payments = FeeTransaction.objects.all()

            else:
                return Response({'error': "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

            serializer = FeeTransactionSerializer(payments, many=True)
            return Response({'payments': serializer.data, 'count': payments.count()}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': "Failed to get payments", 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)