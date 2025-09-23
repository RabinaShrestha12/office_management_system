from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import User, Course
from ..serializers import CourseSerializer
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()
#FOR COURSE
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_courses(request):
    try:
        if request.method == 'GET':
            courses = Course.objects.filter(is_active=True).order_by('title')  
            serializer = CourseSerializer(courses, many=True)
            return Response({'courses': serializer.data, 'count': courses.count()}, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            if request.user.role != 'admin':
                return Response({
                    'error': "Permission denied. Admin access required."}, status=status.HTTP_403_FORBIDDEN)

            serializer = CourseSerializer(data=request.data)
            if serializer.is_valid():
                course = serializer.save()
                return Response({
                    'message': "Course created successfully",'course': CourseSerializer(course).data}, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': "Course creation failed",'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': "Failed to manage courses",'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#FOR COURSE BY ID
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_course_by_id(request, course_id):
    try:
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({'error': "Course not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = CourseSerializer(course)
            return Response({'course': serializer.data}, status=status.HTTP_200_OK)

        elif request.method == 'PUT':
            if request.user.role != 'admin':
                return Response({'error': "Permission denied. Admin access required."}, status=status.HTTP_403_FORBIDDEN)

            serializer = CourseSerializer(course, data=request.data, partial=True)
            if serializer.is_valid():
                updated_course = serializer.save()
                return Response({'message': "Course updated successfully",'course': CourseSerializer(updated_course).data}, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': "Course update failed",'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
                    if request.user.role != 'admin':
                        return Response({'error': "Permission denied. Admin access required."}, status=status.HTTP_403_FORBIDDEN)

                    course.delete()
                    return Response({'message': "Course deleted successfully"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': "Failed to manage course", 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

