
from django.urls import path, include
from django.contrib import admin
from . import views
from . import view3
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('login_success', view3.login_success, name='login_success'),
    path('professor_home', views.professor_home, name='professor_home'),
    path('student_home', views.student_home, name='student_home'),
    path('<lectureid>/admin', views.admin, name='admin'),
    path('student/<lectureid>', views.user, name='user'),
    path('', views.home, name='home'),
    path('export/<lectureid>', views.exportcsv, name='exportcsv'),


]
