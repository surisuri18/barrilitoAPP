from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, QDialog,
    QFormLayout, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QDate
from database import Database
from datetime import timedelta

class RegistrosWidget(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        # Cargar ventas con filtro por defecto: Día y fecha actual
        self.combo_filtro.setCurrentText("Día")
        self.date_edit.setDate(QDate.currentDate())
        
        # Cuando cambie filtro o fecha, recargar ventas
        self.combo_filtro.currentTextChanged.connect(self.cargar_ventas)
        self.date_edit.dateChanged.connect(self.cargar_ventas)
        
        self.cargar_ventas()

    def init_ui(self):
        layout = QVBoxLayout()

        # Filtros
        filtros_layout = QHBoxLayout()
        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems(["Día", "Semana", "Mes", "Año"])
        self.combo_filtro.setStyleSheet("font-size: 18px;")
        filtros_layout.addWidget(QLabel("Filtrar por:"))
        filtros_layout.addWidget(self.combo_filtro)

        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setStyleSheet("font-size: 18px;")
        filtros_layout.addWidget(self.date_edit)

        btn_buscar = QPushButton("Buscar")
        btn_buscar.setStyleSheet("""
            font-size: 18px;
            background-color: #4CAF50;      /* verde */
            color: white;                   /* texto blanco */
            border-radius: 10px;            /* bordes redondeados */
            padding: 8px 16px;              /* relleno para tamaño cómodo */
        """)
        btn_buscar.clicked.connect(self.cargar_ventas)
        filtros_layout.addWidget(btn_buscar)
        filtros_layout.addStretch()


        layout.addLayout(filtros_layout)

        # Tabla de ventas
        self.tabla = QTableWidget(0, 3)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Total", "Acciones"])
        self.tabla.setStyleSheet("font-size: 17px;")
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        layout.addWidget(self.tabla)

        # Total vendido
        total_layout = QHBoxLayout()
        self.total_label = QLabel("Total vendido: $0")
        self.total_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #185fbc;")
        total_layout.addWidget(self.total_label)
        total_layout.addStretch()
        layout.addLayout(total_layout)

        self.setLayout(layout)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setColumnWidth(0, 180)  # Fecha
        self.tabla.setColumnWidth(1, 100)  # Total
        self.tabla.setColumnWidth(2, 400)  # Acciones

        # Nueva función para calcular fechas de rango según filtro y fecha base
    def calcular_rango_fechas(self, filtro, fecha):
        from datetime import datetime, timedelta
        if filtro == "Día":
            desde = datetime.combine(fecha, datetime.min.time())
            hasta = datetime.combine(fecha, datetime.max.time())
        elif filtro == "Semana":
            desde = datetime.combine(fecha - timedelta(days=6), datetime.min.time())
            hasta = datetime.combine(fecha, datetime.max.time())
        elif filtro == "Mes":
            desde = datetime.combine(fecha.replace(day=1), datetime.min.time())
            hasta = datetime.combine(fecha, datetime.max.time())
        elif filtro == "Año":
            desde = datetime.combine(fecha.replace(month=1, day=1), datetime.min.time())
            hasta = datetime.combine(fecha, datetime.max.time())
        else:
            desde = hasta = None
        return desde, hasta

    
    def cargar_ventas(self):
        from datetime import datetime
        filtro = self.combo_filtro.currentText()
        fecha_qdate = self.date_edit.date()
        fecha = datetime.combine(fecha_qdate.toPython(), datetime.min.time())

        fecha_desde, fecha_hasta = self.calcular_rango_fechas(filtro, fecha)

        ventas = self.db.obtener_ventas_filtradas(fecha_desde, fecha_hasta)
        self.tabla.setRowCount(len(ventas))

        total_vendido = 0
        for i, venta in enumerate(ventas):
            self.tabla.setItem(i, 0, QTableWidgetItem(venta['fecha']))
            self.tabla.setItem(i, 1, QTableWidgetItem(f"${venta['total']:,}"))
            self.tabla.setRowHeight(i, 80)

            btn_layout = QHBoxLayout()
            btn_detalle = QPushButton("Ver detalle")
            btn_detalle.setStyleSheet("background-color: green; color: black; font-size: 14px;")
            btn_detalle.clicked.connect(lambda checked, venta_id=venta['id']: self.ver_detalle_venta(venta_id))

            btn_editar = QPushButton("Editar")
            btn_editar.setStyleSheet("background-color: orange; color: black; font-size: 14px;")
            btn_editar.clicked.connect(lambda checked, venta_id=venta['id']: self.editar_venta(venta_id))

            btn_eliminar = QPushButton("Eliminar")
            btn_eliminar.setStyleSheet("background-color: red; color: black; font-size: 14px;")
            btn_eliminar.clicked.connect(lambda checked, venta_id=venta['id']: self.eliminar_venta(venta_id))

            btn_layout.addWidget(btn_detalle)
            btn_layout.addWidget(btn_editar)
            btn_layout.addWidget(btn_eliminar)

            contenedor = QWidget()
            contenedor.setLayout(btn_layout)
            self.tabla.setCellWidget(i, 2, contenedor)

            total_vendido += venta['total']

        # Cambiar texto de total vendido según filtro
        texto_total = f"Total vendido"
        if filtro == "Día":
            texto_total = f"Total vendido día"
        elif filtro == "Semana":
            texto_total = f"Total vendido semana"
        elif filtro == "Mes":
            texto_total = f"Total vendido mes"
        elif filtro == "Año":
            texto_total = f"Total vendido año"

        self.total_label.setText(f"{texto_total}: ${total_vendido:,}")

    def ver_detalle_venta(self, venta_id):
        detalle = self.db.obtener_detalle_venta(venta_id)
        if not detalle:
            QMessageBox.warning(self, "Detalle", "No se encontraron detalles.")
            return
        texto = "Productos vendidos:\n"
        for prod in detalle:
            texto += f"- {prod['nombre_producto']} x{prod['cantidad']} @ ${prod['precio_unitario']} = ${prod['subtotal']}\n"
        QMessageBox.information(self, f"Detalle de Venta #{venta_id}", texto)

    def eliminar_venta(self, venta_id):
        res = QMessageBox.question(self, "Eliminar venta", "¿Seguro que deseas eliminar esta venta? Esto devolverá el stock.",
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if res == QMessageBox.Yes:
            self.db.eliminar_venta(venta_id)
            QMessageBox.information(self, "Eliminada", "Venta eliminada y stock actualizado.")
            self.cargar_ventas()

    def editar_venta(self, venta_id):
        detalle = self.db.obtener_detalle_venta(venta_id)
        if not detalle:
            QMessageBox.warning(self, "Editar", "No se encontraron detalles.")
            return
        dlg = EditarVentaDialog(detalle, parent=self)
        if dlg.exec():
            items_actualizados = dlg.get_data()
            self.db.actualizar_venta(venta_id, items_actualizados)
            QMessageBox.information(self, "Editada", "Venta actualizada correctamente.")
            self.cargar_ventas()

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_ventas()


class EditarVentaDialog(QDialog):
    def __init__(self, detalle, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Venta")
        self.detalle = detalle
        layout = QFormLayout()
        self.inputs = []

        for item in detalle:
            cantidad_input = QSpinBox()
            cantidad_input.setMaximum(10000)
            cantidad_input.setValue(item['cantidad'])

            precio_input = QDoubleSpinBox()
            precio_input.setMaximum(1_000_000)
            precio_input.setValue(item['precio_unitario'])

            layout.addRow(f"{item['nombre_producto']} - Cantidad:", cantidad_input)
            layout.addRow(f"{item['nombre_producto']} - Precio unitario:", precio_input)

            self.inputs.append((item['producto_id'], cantidad_input, precio_input))

        btns = QHBoxLayout()
        btn_aceptar = QPushButton("Aceptar")
        btn_aceptar.clicked.connect(self.accept)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btns.addWidget(btn_aceptar)
        btns.addWidget(btn_cancelar)
        layout.addRow(btns)

        self.setLayout(layout)

    def get_data(self):
        items = []
        for producto_id, cantidad_input, precio_input in self.inputs:
            items.append({
                'producto_id': producto_id,
                'cantidad': cantidad_input.value(),
                'precio_unitario': precio_input.value()
            })
        return items
