from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse

from .models import Producto, Categoria
from .forms import ProductoForm, CategoriaForm, UploadFileForm

import pandas as pd
import io

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def dashboard_view(request):
    """Refactored Dashboard: Only displays KPIs and links."""
    productos = Producto.objects.all()
    
    total_productos = productos.count()
    valor_total = sum((p.precio_venta * p.stock) for p in productos)
    stock_bajo_count = sum(1 for p in productos if p.stock <= p.stock_minimo)

    context = {
        'total_productos': total_productos,
        'valor_total': valor_total,
        'stock_bajo_count': stock_bajo_count,
    }
    return render(request, 'inventory/dashboard.html', context)


def product_list_view(request):
    """Paginated product list with search and filter."""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('categoria', '')

    productos = Producto.objects.all().select_related('categoria')

    if search_query:
        productos = productos.filter(
            Q(codigo__icontains=search_query) | 
            Q(nombre__icontains=search_query)
        )
    
    if category_filter:
        productos = productos.filter(categoria__nombre=category_filter)
        
    categorias = Categoria.objects.all()

    # Pagination: 10 per page
    paginator = Paginator(productos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'search_query': search_query,
        'category_filter': category_filter,
    }
    return render(request, 'inventory/product_list.html', context)


def add_category_view(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada con éxito.')
            return redirect('inventory:add_category')
    else:
        form = CategoriaForm()
    
    return render(request, 'inventory/form_category.html', {'form': form, 'title': 'Agregar Categoría'})


def add_product_view(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado con éxito.')
            return redirect('inventory:product_list')
    else:
        form = ProductoForm()
    
    return render(request, 'inventory/form_product.html', {'form': form, 'title': 'Agregar Producto'})


def upload_inventory_view(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo_excel']
            try:
                # Same logic as management command but in memory
                df_productos = pd.read_excel(archivo, sheet_name='PRODUCTO').fillna('')
                df_categorias = pd.read_excel(archivo, sheet_name='CATEGORIAS')
                
                # Categorias
                for _, row in df_categorias.iterrows():
                    nombre_categoria = str(row.get('CATEGORIAS', '')).strip()
                    if nombre_categoria:
                        Categoria.objects.get_or_create(nombre=nombre_categoria)
                
                # Productos
                created_count = 0
                updated_count = 0
                for _, row in df_productos.iterrows():
                    codigo = str(row.get('Codigo', '')).strip()
                    if not codigo: continue
                    
                    cat_nombre = str(row.get('Categoria', '')).strip()
                    cat_obj = None
                    if cat_nombre:
                        cat_obj, _ = Categoria.objects.get_or_create(nombre=cat_nombre)
                        
                    defaults = {
                        'nombre': str(row.get('Producto', '')).strip(),
                        'categoria': cat_obj,
                        'marca': str(row.get('Marca', '')).strip(),
                        'descripcion': str(row.get('Descripción', '')).strip(),
                    }
                    
                    try: defaults['precio_compra'] = float(row.get('Precio Compra', 0))
                    except ValueError: defaults['precio_compra'] = 0
                    
                    try: defaults['precio_venta'] = float(row.get('Precio Venta', 0))
                    except ValueError: defaults['precio_venta'] = 0
                    
                    try: defaults['stock'] = int(row.get('Stock', 0))
                    except ValueError: defaults['stock'] = 0
                    
                    try: defaults['stock_minimo'] = int(row.get('Stock Minimo', 0))
                    except ValueError: defaults['stock_minimo'] = 0

                    obj, created = Producto.objects.update_or_create(codigo=codigo, defaults=defaults)
                    if created: created_count += 1
                    else: updated_count += 1
                
                messages.success(request, f'Inventario cargado: {created_count} nuevos, {updated_count} actualizados.')
                return redirect('inventory:dashboard')
            except Exception as e:
                messages.error(request, f'Error procesando archivo: {e}')
    else:
        form = UploadFileForm()
        
    return render(request, 'inventory/form_upload.html', {'form': form, 'title': 'Subir Inventario'})


def export_excel_view(request):
    """Generates an Excel file from the current database state."""
    productos = Producto.objects.all().select_related('categoria')
    
    data = []
    for p in productos:
        data.append({
            'Codigo': p.codigo,
            'Producto': p.nombre,
            'Categoria': p.categoria.nombre if p.categoria else '',
            'Marca': p.marca,
            'Precio Compra': p.precio_compra,
            'Precio Venta': p.precio_venta,
            'Stock': p.stock,
            'Stock Minimo': p.stock_minimo,
            'Descripción': p.descripcion,
        })
        
    df = pd.DataFrame(data)
    
    # Write to memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='PRODUCTO', index=False)
        
        # Also export categorais
        df_cat = pd.DataFrame([c.nombre for c in Categoria.objects.all()], columns=['CATEGORIAS'])
        df_cat.to_excel(writer, sheet_name='CATEGORIAS', index=False)

    output.seek(0)
    response = HttpResponse(
        output.read(), 
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=inventario_export.xlsx'
    return response


def export_pdf_view(request):
    """Generates a PDF report of the inventory using ReportLab."""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=reporte_inventario.pdf'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph('Reporte de Inventario', styles['Title']))
    elements.append(Spacer(1, 12))

    # Table Data
    data = [['Código', 'Producto', 'Categoría', 'P. Compra', 'P. Venta', 'Stock', 'Estado']]
    
    productos = Producto.objects.all().select_related('categoria')
    for p in productos:
        estado = "OK"
        if p.stock == 0: estado = "AGOTADO"
        elif p.stock <= p.stock_minimo: estado = "BAJO"
            
        data.append([
            p.codigo, 
            p.nombre[:30] + '...' if len(p.nombre) > 30 else p.nombre, # truncate long names
            p.categoria.nombre if p.categoria else 'N/A', 
            f"${p.precio_compra}", f"${p.precio_venta}", 
            str(p.stock), estado
        ])

    table = Table(data, colWidths=[60, 200, 100, 70, 70, 50, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
        ('GRID', (0,0), (-1,-1), 1, colors.white),
    ]))

    elements.append(table)
    doc.build(elements)
    
    return response
