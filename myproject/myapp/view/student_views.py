from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import User, Student
from ..serializers import StudentSerializer, TrainerSerializer,TrainerCourseSerializer
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()
#Profile Created by Admin of Student
@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def create_student_profile(request):
    if request.method == 'POST':
        try:
        # admin le matra student profile banauna paune
            if request.user.role != 'admin':
                return Response({
                    'error': "Permission denied. Admin access required."}, status=status.HTTP_403_FORBIDDEN)
            
            user_id = request.data.get('user_id')
            student_type = request.data.get('student_type')

            if not user_id:
                return Response({'error': "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            if not student_type:
                return Response({'error': "student_type is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Get student user
            try:
                user = User.objects.get(id=user_id, role='student')
            except User.DoesNotExist:
                return Response({'error': "Student user not found"}, status=status.HTTP_404_NOT_FOUND)

            # student profile already xa ki xaina vanera check garne
            if Student.objects.filter(user=user).exists():
                return Response({'error': 'Student profile already exists'}, status=status.HTTP_400_BAD_REQUEST)

            # student profile create garne
            serializer = StudentSerializer(data={
                'student_type': student_type,
                'user': user.id,
                'enrollment_date': request.data.get('enrollment_date'),
                'join_date': request.data.get('join_date'),
                'end_date': request.data.get('end_date')
            })

            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': "Student profile created successfully",
                    'student': serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Invalid data', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': "Failed to create student profile",'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method =='GET':
        try:
            # Only admin can view all student profiles
            if request.user.role != 'admin':
                return Response(
                    {'error': 'Permission denied. Admin access required.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            students = Student.objects.select_related('user').filter(user__role='student')
            serializer = StudentSerializer(students, many=True)

            return Response({
                'students': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': 'Failed to fetch students', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

#To GET student by student_id from student table
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_profile(request, student_id):
    try:
        # If the logged-in user is an admin, they can view any student's profile by ID
        if request.user.role == 'admin':
            try:
                student = Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                return Response({'error': "Student not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = StudentSerializer(student)
            return Response({'student': serializer.data}, status=status.HTTP_200_OK)

        # If the logged-in user is a student, they can only view their own profile
        elif request.user.role == 'student':
            try:
                student_profile = Student.objects.get(user=request.user)
            except Student.DoesNotExist:
                return Response({'error': "Student profile not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = StudentSerializer(student_profile)
            return Response({'student_profile': serializer.data}, status=status.HTTP_200_OK)

        # Any other role is denied
        else:
            return Response({'error': "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    except Exception as e:
        return Response({
            'error': "Failed to get student profile",
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# # ---------------- STUDENT DASHBOARD ----------------
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_student_dashboard(request):
#     try:
#         if request.user.role != 'student':
#             return Response(
#                 {'error': "Permission denied. Student access required."},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         # Access student profile
#         try:
#             student = request.user.student_profile
#         except Student.DoesNotExist:
#             return Response({'error': "Student profile not found"}, status=status.HTTP_404_NOT_FOUND)

#         # All enrollments of this student
#         enrollments = Enrollment.objects.filter(student=student)
#         completed_courses = enrollments.filter(status='completed')
#         active_courses = enrollments.filter(status='enrolled')

#         # Courses details
#         courses_data = [
#             {
#                 'course_title': enrollment.course.title,
#                 'course_category': enrollment.course.category,
#                 'trainer_name': enrollment.trainer.user.get_full_name() if enrollment.trainer else None,
#                 'enrollment_date': enrollment.enrollment_date,
#                 'status': enrollment.status
#             }
#             for enrollment in enrollments
#         ]

#         # Total trainers assigned to this student
#         assigned_trainers = TrainerCourse.objects.filter(
#             course__in=[en.course for en in enrollments],
#             trainer__in=[en.trainer for en in enrollments if en.trainer]
#         ).distinct()

#         # Dashboard summary
#         dashboard_data = {
#             'total_enrollments': enrollments.count(),
#             'active_courses': active_courses.count(),
#             'completed_courses': completed_courses.count(),
#             'assigned_trainers': assigned_trainers.count(),
#             'courses': courses_data
#         }

#         return Response({'dashboard': dashboard_data}, status=status.HTTP_200_OK)

#     except Exception as e:
#         return Response(
#             {'error': "Failed to get student dashboard", 'details': str(e)},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )


