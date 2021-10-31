from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('register/', views.register, name='register'),
    path('login/', views.loginUser, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('anonymous/', views.anonymousLogin, name='anonymous'),

    path('room/<int:pk>', views.room, name='room'),
    path('history/', views.history, name='history'),
    path('delete/<int:pk>', views.delete, name='delete'),
]
