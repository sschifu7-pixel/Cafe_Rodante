from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cliente/buscar/', views.buscar_cliente, name='buscar_cliente'),
    path('cliente/registrar/', views.registrar_cliente, name='registrar_cliente'),
    path('cliente/<str:nfc_uid>/', views.cliente_dashboard, name='cliente_dashboard'),
    path('cliente/<str:nfc_uid>/historial/', views.cliente_historial, name='cliente_historial'),
    path('cliente/<str:nfc_uid>/canjear/', views.cliente_canjear, name='cliente_canjear'),
    path('cliente/<str:nfc_uid>/perfil/', views.cliente_perfil, name='cliente_perfil'),
    path('cliente/<str:nfc_uid>/registrar-compra/', views.registrar_compra, name='registrar_compra'),
    path('cliente/<str:nfc_uid>/realizar-canje/', views.realizar_canje, name='realizar_canje'),
]
