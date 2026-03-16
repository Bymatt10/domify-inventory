from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('productos/', views.product_list_view, name='product_list'),
    path('agregar-producto/', views.add_product_view, name='add_product'),
    path('agregar-categoria/', views.add_category_view, name='add_category'),
    path('subir-inventario/', views.upload_inventory_view, name='upload_inventory'),
    path('exportar/excel/', views.export_excel_view, name='export_excel'),
    path('exportar/pdf/', views.export_pdf_view, name='export_pdf'),
]
