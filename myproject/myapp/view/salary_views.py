from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from ..models import TrainerSalary, Trainer
from ..serializers import TrainerSalarySerializer

# ---------------- CREATE / GET ALL ----------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def trainer_salaries(request):
    if request.method == 'GET':
        try:
            if request.user.role == 'trainer':
                if hasattr(request.user, 'trainer_profile'):
                    trainer = request.user.trainer_profile
                    salaries = TrainerSalary.objects.filter(trainer=trainer).order_by('-month')
                else:
                    return Response({'error': "Trainer profile not found"}, status=status.HTTP_404_NOT_FOUND)
            elif request.user.role == 'admin':
                trainer_id = request.GET.get('trainer_id')
                if trainer_id:
                    try:
                        trainer = Trainer.objects.get(id=trainer_id)
                        salaries = TrainerSalary.objects.filter(trainer=trainer).order_by('-month')
                    except Trainer.DoesNotExist:
                        return Response({'error': "Trainer not found"}, status=status.HTTP_404_NOT_FOUND)
                else:
                    salaries = TrainerSalary.objects.all().order_by('-month')
            else:
                return Response({'error': "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

            serializer = TrainerSalarySerializer(salaries, many=True)
            return Response({'salaries': serializer.data, 'count': salaries.count()}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': "Failed to get trainer salaries", 'details': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'POST':
        try:
            trainer_id = request.data.get('trainer')
            salary_type = request.data.get('salary_type')
            month_str = request.data.get('month')
            payment_date_str = request.data.get('payment_date')
            base_amount = request.data.get('base_amount')
            paid_amount = Decimal(request.data.get('paid_amount', '0.00'))
            completed_students_count = request.data.get('completed_students_count')
            percentage_ratio = request.data.get('percentage_ratio')

            # Validate trainer
            try:
                trainer = Trainer.objects.get(id=trainer_id)
            except Trainer.DoesNotExist:
                return Response({'error': "Trainer not found"}, status=status.HTTP_404_NOT_FOUND)

            # Validate base_amount
            if base_amount is None:
                return Response({'error': "base_amount cannot be null"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                base_amount = Decimal(base_amount)
            except:
                return Response({'error': "Invalid base_amount format"}, status=status.HTTP_400_BAD_REQUEST)
            if base_amount <= 0:
                return Response({'error': "base_amount cannot be zero or negative"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate month
            try:
                month = datetime.strptime(month_str, "%Y-%m-%d").date()
            except (TypeError, ValueError):
                return Response({"error": "Invalid month format. Use YYYY-MM-DD"}, status=400)

            # Validate payment_date
            try:
                payment_date = datetime.strptime(payment_date_str, "%Y-%m-%d").date()
            except (TypeError, ValueError):
                return Response({"error": "Invalid payment_date format. Use YYYY-MM-DD"}, status=400)

            # ---------------- CALCULATE TOTAL & DUE AMOUNT ----------------
            if salary_type == "FIXED":
                total_amount = base_amount
                completed_students_count_val = None
                percentage_ratio_val = None

            elif salary_type == "PERCENTAGE":
                # Validate completed_students_count
                if completed_students_count is None or int(completed_students_count) <= 0:
                    return Response({'error': "completed_students_count cannot be null or zero for PERCENTAGE type"},
                                    status=status.HTTP_400_BAD_REQUEST)
                completed_students_count = int(completed_students_count)

                # Validate percentage_ratio
                if percentage_ratio is None or Decimal(percentage_ratio) <= 0:
                    return Response({'error': "percentage_ratio cannot be null or zero for PERCENTAGE type"},
                                    status=status.HTTP_400_BAD_REQUEST)
                if isinstance(percentage_ratio, str):
                    percentage_ratio = percentage_ratio.replace('%', '').strip()
                try:
                    percentage_ratio = Decimal(percentage_ratio)
                except:
                    return Response({'error': "Invalid percentage_ratio format"}, status=status.HTTP_400_BAD_REQUEST)

                total_amount = base_amount * Decimal(completed_students_count) * (percentage_ratio / Decimal('100'))
                completed_students_count_val = completed_students_count
                percentage_ratio_val = percentage_ratio

            else:
                return Response({"error": "Invalid salary type"}, status=status.HTTP_400_BAD_REQUEST)

            # Round total_amount
            total_amount = total_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calculate due_amount
            due_amount = max(total_amount - paid_amount, Decimal('0.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Determine salary_status automatically
            salary_status = 'paid' if due_amount == Decimal('0.00') else 'pending'

            # Prepare data for serializer
            data = {
                "trainer": trainer.id,
                "salary_type": salary_type,
                "month": month,
                "payment_date": payment_date,
                "base_amount": base_amount,
                "total_amount": total_amount,
                "completed_students_count": completed_students_count_val,
                "salary_status": salary_status,
                "paid_amount": paid_amount,
                "due_amount": due_amount,
                "percentage_ratio": percentage_ratio_val
            }

            serializer = TrainerSalarySerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': "Failed to create trainer salary", 'details': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------- GET / PUT / DELETE BY ID ----------------
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def trainer_salary_by_id(request, salary_id):
    try:
        try:
            salary = TrainerSalary.objects.get(id=salary_id)
        except TrainerSalary.DoesNotExist:
            return Response({'error': "Salary record not found"}, status=status.HTTP_404_NOT_FOUND)

        # -------- GET --------
        if request.method == 'GET':
            serializer = TrainerSalarySerializer(salary)
            return Response({'salary': serializer.data}, status=status.HTTP_200_OK)

        # -------- PUT --------
        elif request.method == 'PUT':
            if request.user.role != 'admin':
                return Response({'error': "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

            trainer_id = request.data.get('trainer')
            salary_type = request.data.get('salary_type', salary.salary_type)
            month = request.data.get('month')
            base_amount = request.data.get('base_amount')
            completed_students_count = request.data.get('completed_students_count')
            paid_amount = request.data.get('paid_amount')
            percentage_ratio = request.data.get('percentage_ratio')
            payment_date_str = request.data.get('payment_date')

            # Update trainer
            if trainer_id:
                try:
                    salary.trainer = Trainer.objects.get(id=trainer_id)
                except Trainer.DoesNotExist:
                    return Response({'error': "Trainer not found"}, status=status.HTTP_404_NOT_FOUND)

            # Update month
            if month:
                try:
                    salary.month = datetime.strptime(month, "%Y-%m-%d").date()
                except ValueError:
                    return Response({"error": "Invalid month format. Use YYYY-MM-DD"}, status=400)

            # Update payment_date
            if payment_date_str:
                try:
                    salary.payment_date = datetime.strptime(payment_date_str, "%Y-%m-%d").date()
                except ValueError:
                    return Response({"error": "Invalid payment_date format. Use YYYY-MM-DD"}, status=400)

            # Update numeric fields with validations
            if base_amount is not None:
                try:
                    base_amount = Decimal(base_amount)
                    if base_amount <= 0:
                        return Response({'error': "base_amount cannot be zero or negative"}, status=status.HTTP_400_BAD_REQUEST)
                    salary.base_amount = base_amount
                except:
                    return Response({'error': "Invalid base_amount format"}, status=status.HTTP_400_BAD_REQUEST)

            if salary_type == "PERCENTAGE":
                if completed_students_count is None or int(completed_students_count) <= 0:
                    return Response({'error': "completed_students_count cannot be null or zero for PERCENTAGE type"},
                                    status=status.HTTP_400_BAD_REQUEST)
                salary.completed_students_count = int(completed_students_count)

                if percentage_ratio is None or Decimal(percentage_ratio) <= 0:
                    return Response({'error': "percentage_ratio cannot be null or zero for PERCENTAGE type"},
                                    status=status.HTTP_400_BAD_REQUEST)
                if isinstance(percentage_ratio, str):
                    percentage_ratio = percentage_ratio.replace('%', '').strip()
                try:
                    salary.percentage_ratio = Decimal(percentage_ratio)
                except:
                    return Response({'error': "Invalid percentage_ratio format"}, status=status.HTTP_400_BAD_REQUEST)

            # Update paid_amount
            if paid_amount is not None:
                salary.paid_amount = Decimal(paid_amount)

            # ---------------- CALCULATE TOTAL & DUE AMOUNT ----------------
            if salary_type == "FIXED":
                salary.total_amount = salary.base_amount
                salary.completed_students_count = None
                salary.percentage_ratio = None
            elif salary_type == "PERCENTAGE":
                salary.total_amount = (salary.base_amount * Decimal(salary.completed_students_count) *
                                       (salary.percentage_ratio / Decimal('100')))
            else:
                return Response({"error": "Invalid salary type"}, status=status.HTTP_400_BAD_REQUEST)

            salary.total_amount = salary.total_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            salary.due_amount = max(salary.total_amount - salary.paid_amount, Decimal('0.00')).quantize(Decimal('0.01'))

            # ---------------- AUTOMATIC SALARY STATUS ----------------
            salary.salary_status = 'paid' if salary.due_amount == Decimal('0.00') else 'pending'
            salary.salary_type = salary_type
            salary.save()

            serializer = TrainerSalarySerializer(salary)
            return Response({'salary': serializer.data, 'message': "Salary updated successfully"}, status=status.HTTP_200_OK)

        # -------- DELETE --------
        elif request.method == 'DELETE':
            if request.user.role != 'admin':
                return Response({'error': "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
            salary.delete()
            return Response({'message': "Salary deleted successfully"}, status=status.HTTP_200_OK)

        return Response({'error': "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    except Exception as e:
        return Response({'error': "Failed to process salary record", 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
