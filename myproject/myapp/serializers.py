from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Trainer, TrainerSalary, ClassSchedule

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'role', 'address', 'phone', 'created_at', 'updated_at'
        ]

        
class TrainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        fields = '__all__'

class TrainerSalarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerSalary
        fields='__all__'


class ClassScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSchedule
        fields = '__all__'