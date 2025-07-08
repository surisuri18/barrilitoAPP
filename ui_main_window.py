# ui_main_window.py
from PySide6.QtWidgets import QApplication, QWidget, QTabWidget, QVBoxLayout
from ui_inventario import InventarioWidget
from ui_vender import VenderWidget
from ui_registros import RegistrosWidget
from database import Database

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimarket POS - Sistema de Venta e Inventario")
        self.resize(1100, 700)

        self.db = Database()

        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { font-size: 22px; height: 50px; width: 240px; }")

        self.tab_inventario = InventarioWidget(self.db)
        self.tab_vender = VenderWidget(self.db)
        self.tab_registros = RegistrosWidget(self.db)

        self.tabs.addTab(self.tab_inventario, "Inventario")
        self.tabs.addTab(self.tab_vender, "Vender")
        self.tabs.addTab(self.tab_registros, "Registros de Ventas")

        layout.addWidget(self.tabs)
        self.setLayout(layout)
