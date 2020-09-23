from django.urls import path
from . import views
urlpatterns = [
    path('', views.index),
    path('data/', views.data),
    path('study/', views.study),
    path('GT/', views.GT),
    path('diagnosis/', views.diagnosis),
]