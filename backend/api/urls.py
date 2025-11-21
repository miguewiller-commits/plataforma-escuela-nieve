from django.urls import path
from . import views
from .views import EmailTokenObtainPairView, MisClasesHoyView

urlpatterns = [
    path("login/", views.api_login, name="api_login"),
    path("instructor/clases/", views.api_clases_instructor, name="api_clases_instructor"),
    path('login/', EmailTokenObtainPairView.as_view(), name='instructor_login'),
    path('clases/hoy/', MisClasesHoyView.as_view(), name='mis_clases_hoy'),
]
