
from django.urls import path, include
from django.contrib import admin
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
<<<<<<< HEAD
    path('admin/', admin.site.urls),
    #path('login-prof', views.loginProf),
    #path('login-student', views.loginStudent),
=======
    path('status/', views.status, name='status'),
>>>>>>> 8d74bf2889b2d8c9256fec0e59a5c2fa6f91c221
    path('professor_home', views.professor_home, name='professor_home'),
    path('student_home', views.student_home, name='student_home'),
    path('<roomid>/admin', views.admin, name='admin'),
    path('student/<roomid>', views.user, name='user'),
    path('', views.home, name='home'),
    path('export/<roomid>', views.exportcsv, name='exportcsv'),


]
