from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from ..models import Trainer, Course, TrainerCourse
from ..serializers import TrainerCourseSerializer

@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def assign_course_to_trainer(request):
    # ---------------- POST: Assign course to trainer ----------------
    if request.method == 'POST':
        try:
            if request.user.role != 'admin':
                return Response({'error': "Permission denied. Admin access required."}, status=status.HTTP_403_FORBIDDEN)

            trainer_id = request.data.get('trainer_id')
            course_id = request.data.get('course_id')

            if not trainer_id or not course_id:
                return Response({'error': "trainer_id and course_id are required"}, status=status.HTTP_400_BAD_REQUEST)

            trainer = Trainer.objects.get(id=trainer_id)
            course = Course.objects.get(id=course_id)

            if TrainerCourse.objects.filter(trainer=trainer, course=course).exists():
                return Response({'error': "Trainer already assigned to this course"}, status=status.HTTP_400_BAD_REQUEST)

            trainer_course = TrainerCourse.objects.create(trainer=trainer, course=course)
            serializer = TrainerCourseSerializer(trainer_course)
            return Response({'message': "Course assigned to trainer successfully", 'assignment': serializer.data}, status=status.HTTP_201_CREATED)

        except Trainer.DoesNotExist:
            return Response({'error': "Trainer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Course.DoesNotExist:
            return Response({'error': "Course not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': "Failed to assign course to trainer", 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------------- GET: Retrieve all trainer-course assignments ----------------
    elif request.method == 'GET':
        try:
            assignments = TrainerCourse.objects.all()
            serializer = TrainerCourseSerializer(assignments, many=True)
            return Response({'trainer_courses': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': "Failed to fetch trainer courses", 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
