
from django.urls import path, include
from django.contrib import admin
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    #path('login-prof', views.loginProf),
    #path('login-student', views.loginStudent),
    path('professor_home', views.professor_home, name='professor_home'),
    path('student_home', views.student_home, name='student_home'),
    path('<roomid>/admin', views.admin, name='admin'),
    path('<roomid>', views.user, name='user'),
    path('', views.home, name='home'),
    path('export/<roomid>', views.exportcsv, name='exportcsv'),
    path('status/', views.status, name='status')

]
