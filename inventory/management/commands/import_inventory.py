import pandas as pd
from django.core.management.base import BaseCommand
from inventory.models import Categoria, Producto

class Command(BaseCommand):
    help = 'Import inventory data from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_path', type=str, help='Path to the Excel file (inventario.xlsx)')

    def handle(self, *args, **kwargs):
        excel_path = kwargs['excel_path']
        self.stdout.write(f"Leyendo archivo: {excel_path}")

        try:
            # Load the PRODUCTO sheet
            df_productos = pd.read_excel(excel_path, sheet_name='PRODUCTO')
            # Fill NaNs with appropriate values or empty strings
            df_productos = df_productos.fillna('')
            
            # Load the CATEGORIAS sheet to ensure we have all categories
            # The excel check showed 'CATEGORIAS' sheet exists.
            df_categorias = pd.read_excel(excel_path, sheet_name='CATEGORIAS')
            
            # 1. Import Categorias
            self.stdout.write("Importando categorías...")
            for _, row in df_categorias.iterrows():
                nombre_categoria = str(row.get('CATEGORIAS', '')).strip()
                if nombre_categoria:
                    Categoria.objects.get_or_create(nombre=nombre_categoria)
            
            # 2. Import Productos
            self.stdout.write("Importando productos...")
            productos_creados = 0
            productos_actualizados = 0

            for _, row in df_productos.iterrows():
                codigo = str(row.get('Codigo', '')).strip()
                if not codigo:
                    continue
                
                nombre = str(row.get('Producto', '')).strip()
                marca = str(row.get('Marca', '')).strip()
                desc = str(row.get('Descripción', '')).strip()
                
                cat_nombre = str(row.get('Categoria', '')).strip()
                categoria_obj = None
                if cat_nombre:
                    categoria_obj, _ = Categoria.objects.get_or_create(nombre=cat_nombre)

                # Parsing numbers safely
                try:
                    p_compra = float(row.get('Precio Compra', 0))
                except ValueError:
                    p_compra = 0
                
                try:
                    p_venta = float(row.get('Precio Venta', 0))
                except ValueError:
                    p_venta = 0
                
                try:
                    stock = int(row.get('Stock', 0))
                except ValueError:
                    stock = 0
                
                try:
                    stock_min = int(row.get('Stock Minimo', 0))
                except ValueError:
                    stock_min = 0

                obj, created = Producto.objects.update_or_create(
                    codigo=codigo,
                    defaults={
                        'nombre': nombre,
                        'categoria': categoria_obj,
                        'marca': marca,
                        'precio_compra': p_compra,
                        'precio_venta': p_venta,
                        'stock': stock,
                        'stock_minimo': stock_min,
                        'descripcion': desc
                    }
                )
                
                if created:
                    productos_creados += 1
                else:
                    productos_actualizados += 1

            self.stdout.write(self.style.SUCCESS(f"Importación completada con éxito. Creados: {productos_creados}, Actualizados: {productos_actualizados}."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importando datos: {e}"))
