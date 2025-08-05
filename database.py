# database.py
import sqlite3
from datetime import datetime


import sys
import os

def get_db_path(filename):
    if getattr(sys, 'frozen', False):
        # Ejecutable creado por PyInstaller
        base_path = sys._MEIPASS
    else:
        # Ejecución en desarrollo
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)


DB_FILE = get_db_path("minimarket.db")

class Database:
    def __init__(self, db_file=DB_FILE):
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row  # Para acceder por nombre
        self._create_tables()

    def _create_tables(self):
        """Crea las tablas si no existen."""
        cursor = self.conn.cursor()
        # Tabla de productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                codigo TEXT,
                precio_compra INTEGER NOT NULL,
                precio_venta INTEGER NOT NULL,
                cantidad REAL NOT NULL
            )
        ''')
        # Tabla de ventas (cabecera)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                total INTEGER NOT NULL
            )
        ''')
        # Tabla detalle de ventas (items de cada venta)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detalles_venta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                nombre_producto TEXT NOT NULL,
                cantidad REAL NOT NULL,
                precio_unitario INTEGER NOT NULL,
                subtotal INTEGER NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas(id)
                -- NO hacemos referencia a productos para que no dependa del producto
            );
        ''')
        self.conn.commit()

    # CRUD Productos
    def agregar_producto(self, nombre, codigo, precio_compra, precio_venta, cantidad):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO productos (nombre, codigo, precio_compra, precio_venta, cantidad)
            VALUES (?, ?, ?, ?, ?)
        ''', (nombre, codigo, precio_compra, precio_venta, cantidad))
        self.conn.commit()

    def actualizar_producto(self, producto_id, nombre, codigo, precio_compra, precio_venta, cantidad):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE productos SET nombre=?, codigo=?, precio_compra=?, precio_venta=?, cantidad=?
            WHERE id=?
        ''', (nombre, codigo, precio_compra, precio_venta, cantidad, producto_id))
        self.conn.commit()

    def actualizar_venta(self, venta_id, items_actualizados):
        cursor = self.conn.cursor()

        # Obtener detalles actuales
        cursor.execute("SELECT producto_id, cantidad FROM detalles_venta WHERE venta_id=?", (venta_id,))
        detalles_anteriores = cursor.fetchall()

        # Revertir stock anterior
        for item in detalles_anteriores:
            
            cursor.execute(
                "UPDATE productos SET cantidad = cantidad + ? WHERE id = ?",
                (item["cantidad"], item["producto_id"])
            )

        # Eliminar detalles antiguos
        cursor.execute("DELETE FROM detalles_venta WHERE venta_id=?", (venta_id,))

        total_nuevo = 0

        # Insertar nuevos detalles y descontar stock
        for item in items_actualizados:
            subtotal = item['cantidad'] * item['precio_unitario']
            total_nuevo += subtotal

            # obtenemos de nuevo el nombre antes de insertar
            prod = self.obtener_producto_por_id(item['producto_id'])
            nombre = prod['nombre'] if prod else "Producto eliminado"

            cursor.execute(
                '''
                INSERT INTO detalles_venta
                (venta_id, producto_id, nombre_producto, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (
                venta_id,
                item['producto_id'],
                nombre,
                item['cantidad'],
                item['precio_unitario'],
                subtotal
                )
            )

            # Descontar stock
            cursor.execute(
                "UPDATE productos SET cantidad = cantidad - ? WHERE id = ?",
                (item['cantidad'], item['producto_id'])
            )

        # Actualizar total en cabecera
        cursor.execute("UPDATE ventas SET total = ? WHERE id = ?", (total_nuevo, venta_id))

        self.conn.commit()


    def eliminar_venta(self, venta_id):
        cursor = self.conn.cursor()

        # Obtener detalle de la venta
        cursor.execute("SELECT producto_id, cantidad FROM detalles_venta WHERE venta_id=?", (venta_id,))
        detalles = cursor.fetchall()

        # Devolver stock
        for item in detalles:
            cursor.execute(
                "UPDATE productos SET cantidad = cantidad + ? WHERE id = ?",
                (item["cantidad"], item["producto_id"])
            )

        # Eliminar detalles
        cursor.execute("DELETE FROM detalles_venta WHERE venta_id=?", (venta_id,))
        # Eliminar cabecera
        cursor.execute("DELETE FROM ventas WHERE id=?", (venta_id,))

        self.conn.commit()


    def obtener_producto_por_codigo(self, codigo):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM productos WHERE codigo=?", (codigo,))
        row = cur.fetchone()
        return dict(row) if row else None


    def eliminar_producto(self, producto_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM productos WHERE id=?', (producto_id,))
        self.conn.commit()

    def obtener_productos(self, filtro=None):
        cursor = self.conn.cursor()
        if filtro:
            filtro = f"%{filtro}%"
            cursor.execute('''
                SELECT * FROM productos
                WHERE nombre LIKE ? OR codigo LIKE ?
                ORDER BY nombre ASC
            ''', (filtro, filtro))
        else:
            cursor.execute('SELECT * FROM productos ORDER BY nombre ASC')
        return cursor.fetchall()

    # CRUD Ventas y detalles
    def registrar_venta(self, items):
        """items: lista de dicts {'producto_id', 'cantidad', 'precio_unitario', 'subtotal'}"""
        cursor = self.conn.cursor()
        total = sum(item['subtotal'] for item in items)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 1. Cabecera venta
        cursor.execute('INSERT INTO ventas (fecha, total) VALUES (?, ?)', (fecha, total))
        venta_id = cursor.lastrowid
        # 2. Detalle y stock
        for item in items:
            prod = self.obtener_producto_por_id(item['producto_id'])
            nombre_producto = prod['nombre'] if prod else "Producto eliminado"
            cursor.execute('''
                INSERT INTO detalles_venta 
                (venta_id, producto_id, nombre_producto, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                venta_id,
                item['producto_id'],
                nombre_producto,
                item['cantidad'],
                item['precio_unitario'],
                item['subtotal']
            ))
            # 3. Descontar stock
            cursor.execute('''
                UPDATE productos SET cantidad = cantidad - ? WHERE id = ?
            ''', (item['cantidad'], item['producto_id']))
        self.conn.commit()
        return venta_id

    def obtener_ventas(self, fecha_desde=None, fecha_hasta=None):
        cursor = self.conn.cursor()
        query = 'SELECT * FROM ventas'
        params = []
        if fecha_desde and fecha_hasta:
            query += ' WHERE date(fecha) BETWEEN ? AND ?'
            params = [fecha_desde, fecha_hasta]
        elif fecha_desde:
            query += ' WHERE date(fecha) >= ?'
            params = [fecha_desde]
        elif fecha_hasta:
            query += ' WHERE date(fecha) <= ?'
            params = [fecha_hasta]
        query += ' ORDER BY fecha DESC'
        cursor.execute(query, params)
        return cursor.fetchall()

    def obtener_detalle_venta(self, venta_id):
        cur = self.conn.cursor()
        cur.execute('''
            SELECT producto_id,
                nombre_producto,
                cantidad,
                precio_unitario,
                subtotal
            FROM detalles_venta
            WHERE venta_id = ?
        ''', (venta_id,))
        return [dict(row) for row in cur.fetchall()]



    # Utilidades para backup/exportar
    def exportar_productos_excel(self, file_path):
        import pandas as pd
        productos = self.obtener_productos()
        df = pd.DataFrame(productos, columns=productos[0].keys() if productos else [])
        df.to_excel(file_path, index=False)

    def exportar_ventas_excel(self, file_path):
        import pandas as pd
        ventas = self.obtener_ventas()
        df = pd.DataFrame(ventas, columns=ventas[0].keys() if ventas else [])
        df.to_excel(file_path, index=False)

     # ---- CRUD Productos ----

    def obtener_producto_por_id(self, prod_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM productos WHERE id=?", (prod_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def agregar_producto(self, data):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO productos (nombre, codigo, precio_compra, precio_venta, cantidad) VALUES (?, ?, ?, ?, ?)",
            (data['nombre'], data['codigo'], data['precio_compra'], data['precio_venta'], data['cantidad'])
        )
        self.conn.commit()

    def actualizar_producto(self, prod_id, data):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE productos SET nombre=?, codigo=?, precio_compra=?, precio_venta=?, cantidad=? WHERE id=?",
            (data['nombre'], data['codigo'], data['precio_compra'], data['precio_venta'], data['cantidad'], prod_id)
        )
        self.conn.commit()

    def eliminar_producto(self, prod_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM productos WHERE id=?", (prod_id,))
        self.conn.commit()

    # ---- CRUD Ventas (solo estructura, puedes completar luego) ----

    def obtener_ventas_filtradas(self, fecha_desde, fecha_hasta):
        cur = self.conn.cursor()
        q = "SELECT * FROM ventas WHERE datetime(fecha) BETWEEN ? AND ?"
        params = (fecha_desde.strftime("%Y-%m-%d %H:%M:%S"), fecha_hasta.strftime("%Y-%m-%d %H:%M:%S"))
        cur.execute(q, params)
        ventas = [dict(row) for row in cur.fetchall()]
        return ventas


    def close(self):
        self.conn.close()

