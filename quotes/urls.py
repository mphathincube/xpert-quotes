from django.urls import path
from . import views

urlpatterns = [
    path('', views.add_quote, name='add_quote'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/<int:client_id>/', views.client_detail, name='client_detail'),
    path('clients/<int:client_id>/edit/',
         views.edit_client, name='edit_client'),
    path('quotes/<int:quote_id>/edit/', views.edit_quote, name='edit_quote'),
    path('quote-history/', views.quote_history, name='quote_history'),
    path('quotes/<int:quote_id>/pdf/',
         views.generate_quote_pdf, name='generate_quote_pdf'),
]
