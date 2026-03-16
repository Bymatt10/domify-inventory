from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Categoría")

    def __str__(self):
        return self.nombre

import uuid

class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True, blank=True, verbose_name="Código")
    nombre = models.CharField(max_length=200, verbose_name="Producto")
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos', verbose_name="Categoría", null=True, blank=True)
    marca = models.CharField(max_length=100, blank=True, null=True, verbose_name="Marca")
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Compra")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Venta")
    stock = models.IntegerField(default=0, verbose_name="Stock")
    stock_minimo = models.IntegerField(default=0, verbose_name="Stock Mínimo")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def save(self, *args, **kwargs):
        if not self.codigo:
            # Generate a code like PRD-12345678
            self.codigo = f"PRD-{str(uuid.uuid4().hex)[:8].upper()}"
        super().save(*args, **kwargs)
