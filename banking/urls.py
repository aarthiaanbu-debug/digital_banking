from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('transfer/', views.transfer_view, name='transfer'),
    path('otp/', views.verify_otp, name='otp'),
    path('history/', views.history, name='history'),
    path('logout/', views.logout_view, name='logout'),
   path('download-pdf/', views.download_pdf, name='download_pdf'),
   path('transfer/', views.transfer_view, name='transfer'),
path('otp/', views.verify_otp, name='otp'),
path('otp/', views.verify_otp, name='otp'),
]