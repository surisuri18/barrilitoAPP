# ui_inventario.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QFormLayout, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt
from database import Database

class InventarioWidget(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Barra de búsqueda
        busq_layout = QHBoxLayout()
        busq_layout.addWidget(QLabel("Buscar producto:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Nombre o código")
        self.search_edit.setStyleSheet("font-size: 18px;")
        self.search_edit.textChanged.connect(self.filtrar_tabla)
        busq_layout.addWidget(self.search_edit)

        btn_add = QPushButton("Añadir producto")
        btn_add.setStyleSheet("font-size: 18px; background-color: #5fb85f; color: white;")
        btn_add.clicked.connect(self.abrir_agregar)
        busq_layout.addWidget(btn_add)
        layout.addLayout(busq_layout)

        # Tabla de productos
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(["Producto", "Código", "P.Compra", "P.Venta", "Cantidad", "Acciones"])
        self.tabla.setStyleSheet("font-size: 17px;")
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        layout.addWidget(self.tabla)

        self.tabla.setColumnWidth(0, 180)  
        self.tabla.setColumnWidth(1, 100) 
        self.tabla.setColumnWidth(2, 250) 
        self.tabla.setColumnWidth(3, 180)  
        self.tabla.setColumnWidth(4, 100) 
        self.tabla.setColumnWidth(5, 250)  

        self.setLayout(layout)
        self.cargar_productos()

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_productos()  # Recargar productos cada vez que se muestra

    def cargar_productos(self):
        productos = self.db.obtener_productos()
        self._p_rows = productos
        self.mostrar_tabla(productos)

    def mostrar_tabla(self, productos):
        self.tabla.setRowCount(len(productos))
        for i, prod in enumerate(productos):
            self.tabla.setItem(i, 0, QTableWidgetItem(prod['nombre']))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(prod['codigo'] or "")))
            self.tabla.setItem(i, 2, QTableWidgetItem(f"${prod['precio_compra']:,}"))
            self.tabla.setItem(i, 3, QTableWidgetItem(f"${prod['precio_venta']:,}"))
            self.tabla.setItem(i, 4, QTableWidgetItem(str(prod['cantidad'])))
            self.tabla.setRowHeight(i, 80)

            # Botón editar
            btn_edit = QPushButton("Editar")
            btn_edit.setStyleSheet("font-size: 15px; background-color: #1e88e5; color: black;")
            btn_edit.clicked.connect(lambda checked, prod_id=prod['id']: self.abrir_editar(prod_id))
            # Botón eliminar
            btn_del = QPushButton("Eliminar")
            btn_del.setStyleSheet("font-size: 15px; background-color: #e53935; color: black;")
            btn_del.clicked.connect(lambda checked, prod_id=prod['id']: self.confirmar_eliminar(prod_id))

            acc_layout = QHBoxLayout()
            acc_layout.addWidget(btn_edit)
            acc_layout.addWidget(btn_del)
            acc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            w = QWidget()
            w.setLayout(acc_layout)
            self.tabla.setCellWidget(i, 5, w)

    def filtrar_tabla(self, texto):
        texto = texto.lower()
        filtrados = [p for p in self._p_rows if texto in p['nombre'].lower() or texto in str(p['codigo']).lower()]
        self.mostrar_tabla(filtrados)

    def abrir_agregar(self):
        dlg = ProductoDialog(parent=self)
        if dlg.exec():
            data = dlg.get_data()
            if not data['nombre'] or not data['precio_compra'] or not data['precio_venta'] or data['cantidad'] is None:
                QMessageBox.warning(self, "Error", "Todos los campos obligatorios.")
                return
            self.db.agregar_producto(data)
            self.cargar_productos()

    def abrir_editar(self, prod_id):
        prod = self.db.obtener_producto_por_id(prod_id)
        if not prod:
            QMessageBox.warning(self, "Error", "Producto no encontrado.")
            return
        dlg = ProductoDialog(producto=prod, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            self.db.actualizar_producto(prod_id, data)
            self.cargar_productos()

    def confirmar_eliminar(self, prod_id):
        res = QMessageBox.question(self, "Eliminar producto", "¿Seguro que deseas eliminar este producto?",
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if res == QMessageBox.Yes:
            self.db.eliminar_producto(prod_id)
            self.cargar_productos()

class CodigoLineEdit(QLineEdit):
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Ignorar EntFer enviado por el lector
            event.ignore()
        else:
            super().keyPressEvent(event)

class ProductoDialog(QDialog):
    def __init__(self, producto=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Producto")
        self.setModal(True)
        layout = QFormLayout()

        self.nombre = QLineEdit(producto['nombre'] if producto else "")
        self.nombre.setStyleSheet("font-size: 18px;")
        self.codigo = QLineEdit(str(producto['codigo']) if producto and producto['codigo'] else "")
        self.codigo.setStyleSheet("font-size: 18px;")

        self.precio_compra = QSpinBox()
        self.precio_compra.setMaximum(1_000_000)
        self.precio_compra.setValue(float(producto['precio_compra']) if producto else 0.0)
        self.precio_compra.setStyleSheet("font-size: 18px;")
        self.precio_compra.setSpecialValueText("")
        self.precio_compra.setButtonSymbols(QSpinBox.NoButtons)
        self.precio_compra.setStyleSheet("font-size: 18px;")

        self.precio_venta = QSpinBox()
        self.precio_venta.setMaximum(1_000_000)
        self.precio_venta.setSpecialValueText("")
        self.precio_venta.setValue(float(producto['precio_venta']) if producto else 0.0)
        self.precio_venta.setButtonSymbols(QSpinBox.NoButtons)
        self.precio_venta.setStyleSheet("font-size: 18px;")

        self.cantidad = QSpinBox()
        self.cantidad.setMaximum(100_000)
        self.cantidad.setSpecialValueText("")
        self.cantidad.setValue(int(producto['cantidad']) if producto else 0)
        self.cantidad.setButtonSymbols(QSpinBox.NoButtons)
        self.cantidad.setStyleSheet("font-size: 18px;")


        layout.addRow("Nombre*", self.nombre)
        layout.addRow("Código", self.codigo)
        layout.addRow("Precio compra*", self.precio_compra)
        layout.addRow("Precio venta*", self.precio_venta)
        layout.addRow("Cantidad*", self.cantidad)

        btns = QHBoxLayout()
        btn_aceptar = QPushButton("Aceptar")
        btn_aceptar.clicked.connect(self.accept)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btns.addWidget(btn_aceptar)
        btns.addWidget(btn_cancelar)
        layout.addRow(btns)
        self.setLayout(layout)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Bloquear Enter para que no cierre el diálogo
            event.ignore()
        else:
            super().keyPressEvent(event)

    def get_data(self):
        return {
            "nombre": self.nombre.text().strip(),
            "codigo": self.codigo.text().strip() or None,
            "precio_compra": int(self.precio_compra.value()),
            "precio_venta": int(self.precio_venta.value()),
            "cantidad": int(self.cantidad.value())
        }
