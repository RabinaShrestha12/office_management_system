from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
 
User = get_user_model()

# Token generation
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),  # Used to get a new access token
        'access': str(refresh.access_token)
    }

# Admin Registration (No login required, but only one admin allowed)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_admin(request):
    try:
        data = request.data
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        phone = data.get('phone')
        address = data.get('address')

        # Ensure only one admin can exist
        if User.objects.filter(role='admin').exists():
            return Response({'err': "An admin account already exists. Please login."}, status=status.HTTP_403_FORBIDDEN)

        if not username or not password or not email:
            return Response({'err': "Username, email, and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone=phone,
            address=address,
            role='admin'
        )
        return Response({'msg': "Admin registered successfully. Please login to continue."}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'err': "Failed to register admin"}, status=status.HTTP_400_BAD_REQUEST)

# Admin Login
@api_view(['POST'])
@permission_classes([AllowAny])
def login_admin(request):
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({'err': "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'err': "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

        if user.role != 'admin':
            return Response({'err': "This login is only for admin."}, status=status.HTTP_403_FORBIDDEN)

        user_auth = authenticate(username=user.username, password=password)
        if user_auth is not None:
            tokens = get_tokens_for_user(user_auth)
            return Response({
                'msg': "Admin login successful.",
                'tokens': tokens,
                'user': {
                    'username': user_auth.username,
                    'role': user_auth.role,
                    'email': user_auth.email
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({'err': "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({'err': "Login failed"}, status=status.HTTP_400_BAD_REQUEST)

#  Register Trainer/Student (Only by logged-in Admin)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_user(request):
    try:
        if not hasattr(request.user, 'role') or request.user.role != 'admin':
            return Response({'err': "Only an admin can register new users."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        phone = data.get('phone')
        role = data.get('role')
        address = data.get('address')

        VALID_ROLES = ['student', 'trainer']
        if role not in VALID_ROLES:
            return Response({'err': "Invalid role. Allowed: student, trainer."}, status=status.HTTP_400_BAD_REQUEST)

        if not username or not password or not email:
            return Response({'err': "Username, email, and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'err': "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'err': "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone=phone,
            address=address,
            role=role
        )
        return Response({'msg': "User registered successfully."}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'err': "Failed to register user"}, status=status.HTTP_400_BAD_REQUEST)

#  Login for Trainer/Student
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    try:
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'err': "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'err': "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

        if user.role not in ['student', 'trainer']:
            return Response({'err': "This login is only for students or trainers."}, status=status.HTTP_403_FORBIDDEN)

        user_auth = authenticate(username=user.username, password=password)
        if user_auth is not None:
            tokens = get_tokens_for_user(user_auth)
            return Response({
                'msg': "Login successful.",
                'tokens': tokens,
                'user': {
                    'username': user_auth.username,
                    'role': user_auth.role,
                    'email': user_auth.email
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({'err': "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({'err':"Login failed"}, status=status.HTTP_400_BAD_REQUEST)

# ----------------- List all trainers and students (Admin only) -----------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_users(request):
    if request.user.role != 'admin':
        return Response({'err': "Only admin can access this."}, status=status.HTTP_403_FORBIDDEN)

    users = User.objects.filter(role__in=['trainer', 'student']).values(
        'id', 'username', 'email', 'role', 'phone', 'address'
    )
    return Response({'users': list(users)}, status=status.HTTP_200_OK)


# get details by id
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def user_detail_crud(request, user_id):
    if request.user.role != 'admin':
        return Response({'err': "Only admin can access this."}, status=status.HTTP_403_FORBIDDEN)

    try:
        user = User.objects.get(id=user_id, role__in=['trainer', 'student'])
    except User.DoesNotExist:
        return Response({'err': "User not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'phone': user.phone,
            'address': user.address,
        }
        return Response({'user': data})

    elif request.method == 'PUT':
        data = request.data
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.contact = data.get('contact', user.contact)
        user.address = data.get('address', user.address)
        user.save()
        return Response({'msg': "User updated successfully."})

    elif request.method == 'DELETE':
        user.delete()
        return Response({'msg': "User deleted successfully."})
    
from django.utils.crypto import get_random_string
from django.core.cache import cache  # to temporarily store tokens
from django.contrib.auth.hashers import make_password

# ----------------- Forgot Password (Request Reset) -----------------
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    try:
        email = request.data.get('email')
        if not email:
            return Response({'err': "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email, role__in=['admin', 'trainer'])
        except User.DoesNotExist:
            return Response({'err': "User not found with this email."}, status=status.HTTP_404_NOT_FOUND)

        # Generate a reset token
        reset_token = get_random_string(32)
        cache.set(f"reset_token_{reset_token}", user.id, timeout=3600)  # valid for 1 hour

        # (For production, send email here instead of returning)
        return Response({
            'msg': "Password reset token generated. Use this token to reset your password.",
            'reset_token': reset_token
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'err': "Failed to process request."}, status=status.HTTP_400_BAD_REQUEST)


# ----------------- Reset Password (Confirm Reset) -----------------
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    try:
        reset_token = request.data.get('reset_token')
        new_password = request.data.get('new_password')

        if not reset_token or not new_password:
            return Response({'err': "Reset token and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user_id = cache.get(f"reset_token_{reset_token}")
        if not user_id:
            return Response({'err': "Invalid or expired reset token."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'err': "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Update password
        user.password = make_password(new_password)
        user.save()

        # Clear the token
        cache.delete(f"reset_token_{reset_token}")

        return Response({'msg': "Password reset successful. Please login with your new password."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'err': "Failed to reset password."}, status=status.HTTP_400_BAD_REQUEST)
