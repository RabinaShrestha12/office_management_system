from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import User, ClassSchedule
from ..serializers import  ClassScheduleSerializer
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()
#FOR COURSE

#FOR CLASS-SCHEDULE
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_schedules(request):
    try:
        if request.method == 'GET':
            schedules = ClassSchedule.objects.all()
            serializer = ClassScheduleSerializer(schedules, many=True)
            return Response({'schedules': serializer.data, 'count': schedules.count()}, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            if request.user.role != 'admin':
                return Response({'error': "Permission denied. Admin access required."}, status=status.HTTP_403_FORBIDDEN)

            serializer = ClassScheduleSerializer(data=request.data)
            if serializer.is_valid():
                schedule = serializer.save()
                return Response({
                    'message': "Schedule created successfully",'schedule': ClassScheduleSerializer(schedule).data}, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': "Schedule creation failed",'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': "Failed to manage schedules",'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_schedule_by_id(request, schedule_id):
    try:
        try:
            schedule = ClassSchedule.objects.get(id=schedule_id)
        except ClassSchedule.DoesNotExist:
            return Response({'error': "Schedule not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = ClassScheduleSerializer(schedule)
            return Response({'schedule': serializer.data}, status=status.HTTP_200_OK)

        elif request.method == 'PUT':
            if request.user.role != 'admin':
                return Response({'error': "Permission denied. Admin access required."}, status=status.HTTP_403_FORBIDDEN)

            serializer = ClassScheduleSerializer(schedule, data=request.data, partial=True)
            if serializer.is_valid():
                updated_schedule = serializer.save()
                return Response({
                    'message': "Schedule updated successfully",'schedule': ClassScheduleSerializer(updated_schedule).data}, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': "Schedule update failed",'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            if request.user.role != 'admin':
                return Response({'error': "Permission denied. Admin access required."}, status=status.HTTP_403_FORBIDDEN)

            schedule.delete()
            return Response({'message': "Schedule deleted successfully"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': "Failed to manage schedule", 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)