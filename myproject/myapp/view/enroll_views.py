from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import Enrollment, Student, Course, Trainer, ClassSchedule
from ..serializers import EnrollmentSerializer
from rest_framework import status
from datetime import datetime

# ------------------ CREATE / GET ENROLLMENTS ------------------
@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def enroll_student(request):
    if request.method == 'POST':
        try:
            if request.user.role != 'admin':
                return Response({'error': "Permission denied. Admin access required."}, status=status.HTTP_403_FORBIDDEN)

            student_id = request.data.get('student_id')
            course_id = request.data.get('course_id')
            trainer_id = request.data.get('trainer_id')
            schedule_id = request.data.get('schedule_id')
            enrollment_date = request.data.get('enrollment_date')

            # Required fields
            if not student_id or not course_id or not enrollment_date:
                return Response({'error': "student_id, course_id, and enrollment_date are required"}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch student and course
            try:
                student = Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                return Response({'error': "Student not found"}, status=status.HTTP_404_NOT_FOUND)

            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                return Response({'error': "Course not found"}, status=status.HTTP_404_NOT_FOUND)

            # Check already enrolled
            if Enrollment.objects.filter(student=student, course=course).exists():
                return Response({'error': "Student is already enrolled in this course"}, status=status.HTTP_400_BAD_REQUEST)

            # Check course capacity
            enrolled_count = Enrollment.objects.filter(course=course, status__in=['enrolled', 'ongoing']).count()
            if course.max_students and enrolled_count >= course.max_students:
                return Response({'error': f"Course is full. Maximum {course.max_students} students allowed."}, status=status.HTTP_400_BAD_REQUEST)

            # Parse enrollment date
            try:
                enrollment_date = datetime.strptime(enrollment_date, "%Y-%m-%d").date()
            except ValueError:
                return Response({'error': "Dates must be in YYYY-MM-DD format"}, status=status.HTTP_400_BAD_REQUEST)

            # Prepare data
            enrollment_data = {
                'student': student,
                'course': course,
                'enrollment_date': enrollment_date,
                'status': 'enrolled'
            }

            if trainer_id:
                try:
                    enrollment_data['trainer'] = Trainer.objects.get(id=trainer_id)
                except Trainer.DoesNotExist:
                    return Response({'error': "Trainer not found"}, status=status.HTTP_404_NOT_FOUND)

            if schedule_id:
                try:
                    enrollment_data['schedule'] = ClassSchedule.objects.get(id=schedule_id)
                except ClassSchedule.DoesNotExist:
                    return Response({'error': "Schedule not found"}, status=status.HTTP_404_NOT_FOUND)

            # FIX: unpack dictionary
            enrollment = Enrollment.objects.create(**enrollment_data)
            serializer = EnrollmentSerializer(enrollment)
            return Response({'message': "Enrollment created successfully", 'enrollment': serializer.data}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': "Failed to enroll student", 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'GET':
        try:
            if request.user.role == 'admin':
                enrollments = Enrollment.objects.all()
            elif request.user.role == 'student':
                enrollments = Enrollment.objects.filter(student__user=request.user)
            else:
                return Response({'error': "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

            serializer = EnrollmentSerializer(enrollments, many=True)
            return Response({'enrollments': serializer.data, 'count': enrollments.count()}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': "Failed to fetch enrollments", 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------ GET / UPDATE / DELETE BY ID ------------------
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def enrollment_by_id(request, enrollment_id):
    try:
        enrollment = Enrollment.objects.get(id=enrollment_id)
    except Enrollment.DoesNotExist:
        return Response({'error': "Enrollment not found"}, status=status.HTTP_404_NOT_FOUND)

    # -------- GET --------
    if request.method == 'GET':
        serializer = EnrollmentSerializer(enrollment)
        return Response({'enrollment': serializer.data}, status=status.HTTP_200_OK)

    # -------- PUT --------
    elif request.method == 'PUT':
        if request.user.role != 'admin':
            return Response({'error': "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        try:
            student_id = request.data.get('student_id')
            course_id = request.data.get('course_id')
            trainer_id = request.data.get('trainer_id')
            schedule_id = request.data.get('schedule_id')
            status_value = request.data.get('status')

            if student_id:
                try:
                    enrollment.student = Student.objects.get(id=student_id)
                except Student.DoesNotExist:
                    return Response({'error': "Student not found"}, status=status.HTTP_404_NOT_FOUND)

            if course_id:
                try:
                    enrollment.course = Course.objects.get(id=course_id)
                except Course.DoesNotExist:
                    return Response({'error': "Course not found"}, status=status.HTTP_404_NOT_FOUND)

            if trainer_id:
                try:
                    enrollment.trainer = Trainer.objects.get(id=trainer_id)
                except Trainer.DoesNotExist:
                    return Response({'error': "Trainer not found"}, status=status.HTTP_404_NOT_FOUND)

            if schedule_id:
                try:
                    enrollment.schedule = ClassSchedule.objects.get(id=schedule_id)
                except ClassSchedule.DoesNotExist:
                    return Response({'error': "Schedule not found"}, status=status.HTTP_404_NOT_FOUND)

            if status_value:
                enrollment.status = status_value

            enrollment.save()
            serializer = EnrollmentSerializer(enrollment)
            return Response({'message': "Enrollment updated successfully", 'enrollment': serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': "Failed to update enrollment", 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # -------- DELETE --------
    elif request.method == 'DELETE':
        if request.user.role != 'admin':
            return Response({'error': "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        enrollment.delete()
        return Response({'message': "Enrollment deleted successfully"}, status=status.HTTP_200_OK)

    return Response({'error': "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
