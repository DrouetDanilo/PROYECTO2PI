import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PySide6.QtCore import Qt
from gui.pantalla_inicio import PantallaInicio
from gui.pantalla_proceso import PantallaProceso
from gui.pantalla_resultados import PantallaResultados
from gui.worker import PipelineWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clasificador y Organizador Automático de Fotografías por Tipo de Escena")
        self.resize(1024, 768)
        self.setMinimumSize(900, 650)
        
        self.output_dir = ""
        self.worker = None

        # Estilo Global Moderno (CSS / QSS)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f1f5f9;
            }
            QLabel {
                font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            }
            QPushButton {
                font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            }
        """)

        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        self.pantalla_inicio = PantallaInicio(self)
        self.pantalla_proceso = PantallaProceso(self)
        self.pantalla_resultados = PantallaResultados(self)

        self.stacked_widget.addWidget(self.pantalla_inicio)
        self.stacked_widget.addWidget(self.pantalla_proceso)
        self.stacked_widget.addWidget(self.pantalla_resultados)

        # Conectar señales
        self.pantalla_inicio.iniciar_procesamiento.connect(self.iniciar_pipeline)
        self.pantalla_proceso.cancelar_procesamiento.connect(self.cancelar_pipeline)
        self.pantalla_resultados.nueva_clasificacion.connect(self.regresar_inicio)
        self.pantalla_resultados.abrir_carpeta_resultados.connect(self.abrir_directorio)

    def iniciar_pipeline(self, input_dir: str, output_dir: str):
        self.output_dir = output_dir
        self.stacked_widget.setCurrentWidget(self.pantalla_proceso)
        
        self.pantalla_proceso.console.clear()
        self.pantalla_proceso.progress_bar.setValue(0)
        
        # Reset de tarjetas de estado de módulo
        self.pantalla_proceso.update_module_state(1, "waiting")
        self.pantalla_proceso.update_module_state(2, "waiting")
        self.pantalla_proceso.update_module_state(3, "waiting")

        # Iniciar Worker
        self.worker = PipelineWorker(input_dir, output_dir)
        self.worker.progress.connect(self.pantalla_proceso.progress_bar.setValue)
        self.worker.log.connect(self.pantalla_proceso.console.append_log)
        self.worker.module_changed.connect(self.pantalla_proceso.update_module_state)
        self.worker.image_processed.connect(self.pantalla_proceso.update_preview_image)
        self.worker.status.connect(self.pantalla_proceso.update_status)
        self.worker.finished.connect(self.procesamiento_completado)
        self.worker.error.connect(self.procesamiento_con_error)
        
        self.worker.start()

    def cancelar_pipeline(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
            QMessageBox.information(self, "Cancelado", "El procesamiento ha sido cancelado.")
            self.regresar_inicio()

    def procesamiento_completado(self, report_path: str):
        self.stacked_widget.setCurrentWidget(self.pantalla_resultados)
        self.pantalla_resultados.load_report(report_path, self.output_dir)

    def procesamiento_con_error(self, message: str):
        QMessageBox.critical(self, "Error en Ejecución", message)
        self.regresar_inicio()

    def regresar_inicio(self):
        self.stacked_widget.setCurrentWidget(self.pantalla_inicio)

    def abrir_directorio(self):
        if self.output_dir:
            os.startfile(str(Path(self.output_dir).resolve()))

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
