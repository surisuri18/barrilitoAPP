# ui_registros.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, QDate
from database import Database

class RegistrosWidget(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()

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
        btn_buscar.setStyleSheet("font-size: 18px;")
        btn_buscar.clicked.connect(self.cargar_ventas)
        filtros_layout.addWidget(btn_buscar)
        filtros_layout.addStretch()

        layout.addLayout(filtros_layout)

        # Tabla de ventas
        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Hora", "Total", "Detalle"])
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

    def cargar_ventas(self):
        filtro = self.combo_filtro.currentText()
        fecha = self.date_edit.date().toPython()  # datetime.date

        ventas = self.db.obtener_ventas_filtradas(filtro, fecha)
        self.tabla.setRowCount(len(ventas))
        total_vendido = 0

        for i, venta in enumerate(ventas):
            self.tabla.setItem(i, 0, QTableWidgetItem(venta['fecha']))
            self.tabla.setItem(i, 1, QTableWidgetItem(venta['hora']))
            self.tabla.setItem(i, 2, QTableWidgetItem(f"${venta['total']:,}"))
            detalle_btn = QPushButton("Ver detalle")
            detalle_btn.setStyleSheet("font-size: 15px;")
            detalle_btn.clicked.connect(lambda checked, venta_id=venta['id']: self.ver_detalle_venta(venta_id))
            self.tabla.setCellWidget(i, 3, detalle_btn)
            total_vendido += venta['total']

        self.total_label.setText(f"Total vendido: ${total_vendido:,}")

    def ver_detalle_venta(self, venta_id):
        # Busca en la base de datos y muestra un mensaje con detalle (personalizable)
        detalle = self.db.obtener_detalle_venta(venta_id)
        if not detalle:
            QMessageBox.warning(self, "Detalle", "No se encontraron detalles.")
            return
        texto = "Productos vendidos:\n"
        for prod in detalle:
            texto += f"- {prod['nombre']} x{prod['cantidad']} @ ${prod['precio_unitario']} = ${prod['subtotal']}\n"
        QMessageBox.information(self, f"Detalle de Venta #{venta_id}", texto)
