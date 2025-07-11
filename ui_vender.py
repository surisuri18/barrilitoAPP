# ui_vender.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QSpinBox, QMessageBox
)
from PySide6.QtCore import Qt
from database import Database

class VenderWidget(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.items_venta = []  # Lista de dicts con producto, cantidad, precio_unitario, subtotal

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Barra de búsqueda/escáner
        buscador_layout = QHBoxLayout()
        self.busqueda_input = QLineEdit()
        self.busqueda_input.setPlaceholderText("Escanea o escribe nombre/código de producto")
        self.busqueda_input.setFixedHeight(40)
        self.busqueda_input.setStyleSheet("font-size: 20px;")
        buscador_layout.addWidget(self.busqueda_input)
        
        buscar_btn = QPushButton("Buscar")
        buscar_btn.setFixedHeight(40)
        buscar_btn.clicked.connect(self.buscar_producto)
        buscador_layout.addWidget(buscar_btn)
        layout.addLayout(buscador_layout)

        # Tabla de productos en la venta
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels([
            "Producto", "Código", "Precio", "Cantidad", "Subtotal"
        ])
        self.tabla.setStyleSheet("font-size: 18px;")
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.tabla)

        # Total
        total_layout = QHBoxLayout()
        self.total_label = QLabel("TOTAL: $0")
        self.total_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #155f03;")
        total_layout.addWidget(self.total_label)
        total_layout.addStretch()
        layout.addLayout(total_layout)

        # Botón registrar venta
        self.btn_registrar = QPushButton("Registrar Venta")
        self.btn_registrar.setStyleSheet("font-size: 24px; background-color: #18a318; color: white;")
        self.btn_registrar.clicked.connect(self.registrar_venta)
        layout.addWidget(self.btn_registrar)

        self.setLayout(layout)
        self.busqueda_input.returnPressed.connect(self.buscar_producto)
        self.tabla.cellDoubleClicked.connect(self.editar_eliminar_item)

    def buscar_producto(self):
        texto = self.busqueda_input.text().strip()
        if not texto:
            QMessageBox.information(self, "Buscar", "Escribe el nombre o código del producto.")
            return
        # Buscar por código exacto primero
        prod = self.db.obtener_producto_por_codigo(texto)
        if prod:
            self.popup_cantidad(prod)
            return
        # Si no es código, busca por nombre similar
        resultados = self.db.obtener_productos(filtro=texto)
        if not resultados:
            QMessageBox.warning(self, "No encontrado", "No se encontró ningún producto.")
        elif len(resultados) == 1:
            self.popup_cantidad(resultados[0])
        else:
            # Si hay varios resultados, muestra lista para elegir
            self.popup_elegir_producto(resultados)

    def popup_cantidad(self, prod):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"¿Cantidad a vender? — {prod['nombre']}")
        dlg.setModal(True)
        layout = QVBoxLayout()
        lbl = QLabel(f"Producto: {prod['nombre']}\nStock disponible: {prod['cantidad']}\nPrecio: ${prod['precio_venta']}")
        lbl.setStyleSheet("font-size: 20px;")
        layout.addWidget(lbl)
        spin = QSpinBox()
        spin.setMinimum(1)
        spin.setMaximum(prod['cantidad'])
        spin.setValue(1)
        spin.setStyleSheet("font-size: 24px;")
        layout.addWidget(spin)
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Confirmar")
        btn_cancel = QPushButton("Cancelar")
        btn_ok.setStyleSheet("font-size: 20px; background: #38ad18; color: white;")
        btn_cancel.setStyleSheet("font-size: 20px; background: #d32f2f; color: white;")
        btn_ok.clicked.connect(lambda: self.agregar_a_venta(prod, spin.value(), dlg))
        btn_cancel.clicked.connect(dlg.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        dlg.setLayout(layout)
        dlg.exec()

    def popup_elegir_producto(self, resultados):
        dlg = QDialog(self)
        dlg.setWindowTitle("Elige un producto")
        layout = QVBoxLayout()
        for prod in resultados:
            btn = QPushButton(f"{prod['nombre']} (Cod: {prod['codigo']}) — Stock: {prod['cantidad']}")
            btn.setStyleSheet("font-size: 18px;")
            btn.clicked.connect(lambda _, p=prod: [dlg.accept(), self.popup_cantidad(p)])
            layout.addWidget(btn)
        dlg.setLayout(layout)
        dlg.exec()

    def agregar_a_venta(self, prod, cantidad, dlg):
        # Si ya está en la lista, suma cantidad
        for item in self.items_venta:
            if item['producto_id'] == prod['id']:
                if item['cantidad'] + cantidad > prod['cantidad']:
                    QMessageBox.warning(self, "Stock insuficiente", "No hay suficiente stock.")
                    return
                item['cantidad'] += cantidad
                item['subtotal'] = item['cantidad'] * item['precio_unitario']
                self.actualizar_tabla()
                dlg.accept()
                return
        # Si es nuevo producto en la venta
        self.items_venta.append({
            'producto_id': prod['id'],
            'nombre': prod['nombre'],
            'codigo': prod['codigo'],
            'precio_unitario': prod['precio_venta'],
            'cantidad': cantidad,
            'subtotal': cantidad * prod['precio_venta']
        })
        self.actualizar_tabla()
        dlg.accept()

    def actualizar_tabla(self):
        self.tabla.setRowCount(len(self.items_venta))
        for i, item in enumerate(self.items_venta):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(item['nombre'])))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(item['codigo'])))
            self.tabla.setItem(i, 2, QTableWidgetItem(f"${item['precio_unitario']}"))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(item['cantidad'])))
            self.tabla.setItem(i, 4, QTableWidgetItem(f"${item['subtotal']}"))
        total = sum(item['subtotal'] for item in self.items_venta)
        self.total_label.setText(f"TOTAL: ${total:,}")

    def editar_eliminar_item(self, row, col):
        item = self.items_venta[row]
        dlg = QDialog(self)
        dlg.setWindowTitle("Editar/Eliminar producto")
        layout = QVBoxLayout()
        lbl = QLabel(f"Producto: {item['nombre']}\nCantidad actual: {item['cantidad']}")
        lbl.setStyleSheet("font-size: 20px;")
        layout.addWidget(lbl)
        spin = QSpinBox()
        spin.setMinimum(1)
        spin.setMaximum(9999)
        spin.setValue(item['cantidad'])
        spin.setStyleSheet("font-size: 24px;")
        layout.addWidget(spin)
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        btn_del = QPushButton("Eliminar")
        btn_cancel = QPushButton("Cancelar")
        btn_ok.setStyleSheet("font-size: 20px; background: #38ad18; color: white;")
        btn_del.setStyleSheet("font-size: 20px; background: #c21807; color: white;")
        btn_cancel.setStyleSheet("font-size: 20px;")
        btn_ok.clicked.connect(lambda: self.actualizar_cantidad(row, spin.value(), dlg))
        btn_del.clicked.connect(lambda: self.eliminar_item(row, dlg))
        btn_cancel.clicked.connect(dlg.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_del)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        dlg.setLayout(layout)
        dlg.exec()

    def actualizar_cantidad(self, row, nueva_cant, dlg):
        item = self.items_venta[row]
        item['cantidad'] = nueva_cant
        item['subtotal'] = nueva_cant * item['precio_unitario']
        self.actualizar_tabla()
        dlg.accept()

    def eliminar_item(self, row, dlg):
        del self.items_venta[row]
        self.actualizar_tabla()
        dlg.accept()

    def registrar_venta(self):
        if not self.items_venta:
            QMessageBox.warning(self, "Venta vacía", "Agrega productos para registrar la venta.")
            return
        # Validar stock
        for item in self.items_venta:
            prod = self.db.obtener_producto_por_id(item['producto_id'])
            if item['cantidad'] > prod['cantidad']:
                QMessageBox.warning(self, "Stock insuficiente", f"No hay suficiente stock para {prod['nombre']}.")
                return
        venta_id = self.db.registrar_venta(self.items_venta)
        self.items_venta.clear()
        self.actualizar_tabla()
        QMessageBox.information(self, "¡Venta registrada!", f"Venta N° {venta_id} registrada exitosamente.")
