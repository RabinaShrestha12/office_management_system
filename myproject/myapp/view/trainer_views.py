from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import User, Trainer
from ..serializers import TrainerSerializer

from rest_framework import status
from django.contrib.auth import get_user_model
#For Trainer

@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def create_trainer_profile(request):
    if request.method == "POST":
        try:
            if request.user.role != 'admin':
                return Response({'error': "Permission denied. Admin access required."}, status=status.HTTP_403_FORBIDDEN)
            
            user_id = request.data.get('user_id')
            trainer_type = request.data.get('trainer_type')
            salary_method = request.data.get('salary_method')
            salary_amount = request.data.get('salary_amount')
            
            if not user_id:
                return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            if not trainer_type:
                return Response({'error': 'trainer_type is required'}, status=status.HTTP_400_BAD_REQUEST)
            if not salary_method:
                return Response({'error': 'salary_method is required'}, status=status.HTTP_400_BAD_REQUEST)
            if salary_amount is None:
                return Response({'error': 'salary_amount is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                user = User.objects.get(id=user_id, role='trainer')
            except User.DoesNotExist:
                return Response({'error': "Trainer user not found"}, status=status.HTTP_404_NOT_FOUND)

            if Trainer.objects.filter(user=user).exists():
                return Response({'error': "Trainer profile already exists"}, status=status.HTTP_400_BAD_REQUEST)

            serializer_data = {
                'user': user.id,
                'trainer_type': trainer_type,
                'salary_method': salary_method,
                'salary_amount': salary_amount,
            }

            serializer = TrainerSerializer(data=serializer_data)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': "Trainer profile created successfully", 'trainer': serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': "Invalid data", 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': "Failed to create trainer profile", 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == "GET":
        try:
            # Only allow admins to access this
            if request.user.role != 'admin':
                return Response(
                    {'error': "Permission denied. Admin access required."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Fetch all trainers
            trainers = Trainer.objects.all()
            serializer = TrainerSerializer(trainers, many=True)
            return Response({'trainers': serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': "Failed to get trainers", 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def trainer_detail_by_id(request, trainer_id):
    try:
        try:
            trainer = Trainer.objects.get(id=trainer_id)
        except Trainer.DoesNotExist:
            return Response({'error': "Trainer profile not found"}, status=status.HTTP_404_NOT_FOUND)

        # GET method
        if request.method == 'GET':
            if request.user.role == 'admin' or trainer.user == request.user:
                serializer = TrainerSerializer(trainer)
                return Response({'trainer': serializer.data}, status=status.HTTP_200_OK)
            return Response({'error': "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        # PUT method
        elif request.method == 'PUT':
            if request.user.role != 'admin' and trainer.user != request.user:
                return Response({'error': "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            serializer = TrainerSerializer(trainer, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': "Trainer profile updated successfully", 'trainer': serializer.data}, status=status.HTTP_200_OK)
            return Response({'error': "Invalid data", 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # DELETE method
        elif request.method == 'DELETE':
            if request.user.role != 'admin':
                return Response({'error': "Permission denied. Admin access required."}, status=status.HTTP_403_FORBIDDEN)
            trainer.delete()
            return Response({'message': "Trainer profile deleted successfully"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': "Failed to process trainer profile", 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
