# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from decimal import Decimal


# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin','Admin'),
        ('student','Student'),
        ('trainer','Trainer'),
    )
    role = models.CharField(max_length=100, choices=ROLE_CHOICES)
    address = models.CharField(max_length=100)
    phone = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class Student(models.Model):
    STUDENT_TYPE = (
        ('intern', 'intern'),
        ('intern+trainer', 'intern+trainer'),
        ('trainer', 'trainer'),
    )
    student_type = models.CharField(max_length=50, choices=STUDENT_TYPE, default='intern')
    enrollment_date = models.DateTimeField()
    join_date = models.DateTimeField()
    end_date = models.DateField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class Trainer(models.Model):
    SALARY_FIXED = 'FIXED'
    SALARY_PERCENTAGE = 'PERCENTAGE'

    SALARY_TYPE_CHOICES = [
        (SALARY_FIXED, 'Fixed'),
        (SALARY_PERCENTAGE, 'Percentage'),
    ]

    TRAINER_TYPE = (
        ('TRAINER', 'trainer'),
        ('TRAINER+DEVELOPER', 'trainer+developer'),
        ('DEVELOPER', 'developer'),
    )

    trainer_type = models.CharField(max_length=200, choices=TRAINER_TYPE, default='trainer')
    salary_method = models.CharField(max_length=200)
    salary_amount = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class Course(models.Model):
    max_students = models.PositiveIntegerField(default = 30)
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    category = models.CharField(max_length=200)
    duration = models.IntegerField()
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    
class TrainerCourse(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

class Enrollment(models.Model):
    STATUS_CHOICES = (
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    enrollment_date = models.DateField(null=True, blank=True)
    schedule = models.ForeignKey('ClassSchedule', null=True, blank=True, on_delete=models.SET_NULL)

     
class ClassSchedule(models.Model):
    shift_type = models.CharField(max_length=200)
    shift_time = models.DateTimeField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)


class FeeTransaction(models.Model):
    METHOD_CHOICES = (
        ('ONLINE', 'Online'),
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    )
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=30, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, )
    payment_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)

    

class TrainerSalary(models.Model):
    SALARY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]

    SALARY_TYPE_CHOICES = [
        ('FIXED', 'Fixed'),
        ('PERCENTAGE', 'Percentage'),
    ]

    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    month = models.DateField(blank=True, null=True)
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    completed_students_count = models.IntegerField(default=0, blank=True, null=True)
    salary_status = models.CharField(max_length=20, choices=SALARY_STATUS_CHOICES, default='pending')
    salary_type = models.CharField(max_length=20, choices=SALARY_TYPE_CHOICES)
    payment_date = models.DateField(blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    percentage_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'),blank=True, null=True)
    

class Certificate(models.Model):
    name=models.CharField(max_length=100)
    company=models.CharField(max_length=500)
    role_field= models.CharField(max_length=500)
    joined_date=models.DateField()
    end_date=models.DateField()
    working_days=models.CharField(max_length=300)
    supervisor_signature=models.ImageField(max_length=300, null=True, blank=True)



