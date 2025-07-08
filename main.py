# main.py
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from ui_main_window import MainWindow  # Asegúrate de crear este archivo después

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Fuente grande y accesible para toda la app
    app.setFont(QFont("Arial", 16))
    
    # Tema claro y fondo blanco (opcional, puedes personalizar luego)
    app.setStyleSheet("""
        QWidget {
            background-color: #fafafa;
            color: #222;
        }
        QLineEdit, QTableWidget, QPushButton {
            font-size: 18px;
        }
        QPushButton {
            padding: 12px 24px;
        }
    """)

    window = MainWindow()  # Esta clase la crearás en ui_main_window.py
    window.setWindowTitle("POS Minimarket - Punto de Venta")
    window.resize(1080, 720)  # Resolución cómoda
    window.show()
    
    sys.exit(app.exec())
