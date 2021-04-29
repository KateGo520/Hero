from django.urls import path
from heroAPP import views
urlpatterns = [
    path('', views.index),
    path('data/', views.data),
    path('study/', views.study),
    path('GT/', views.GT),
    path('diagnosis/', views.diagnosis),
    path('artifacts/', views.artifacts),
]