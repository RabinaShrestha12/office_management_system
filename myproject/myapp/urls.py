from django.urls import path
from .view.auth_views import list_all_users,login_admin,register_admin,register_user,user_detail_crud,login_user, forgot_password, reset_password
from .view.salary_views import trainer_salaries, trainer_salary_by_id
from .view.trainer_views import create_trainer_profile, trainer_detail_by_id

 

urlpatterns = [
    #authentication
    path('login/', login_admin),
    path('register/', register_admin),
    path('login-user/', login_user),
    path('register-user/', register_user),
    path('list/', list_all_users),
    path('list/<int:user_id>', user_detail_crud),
    path('forgotpassword/', forgot_password),
    path('resetpassword/', reset_password),
    #trainer
    path('trainer/<int:trainer_id>',trainer_detail_by_id),
    path('trainer/', create_trainer_profile),
    #salary
    path('trainer-salary/', trainer_salaries),
    path('trainer-salary/<int:salary_id>', trainer_salary_by_id)
    ]