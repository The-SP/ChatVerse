from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.loginUser, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('anonymous/', views.anonymousLogin, name='anonymous'),
    path('chat/', views.chat, name='chat'),
    path('history/', views.history, name='history'),
]
