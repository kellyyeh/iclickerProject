
from django.urls import path, include
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('status/', views.status, name='status'),
    path('professor_home', views.professor_home, name='professor_home'),
    path('student_home', views.student_home, name='student_home'),
    path('<roomid>/admin', views.admin, name='admin'),
    path('student/<roomid>', views.user, name='user'),
    path('', views.home, name='home'),
    path('export/<roomid>', views.exportcsv, name='exportcsv'),


]
