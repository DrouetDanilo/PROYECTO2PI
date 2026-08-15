# Impresión de logs y control de ejecución redireccionados
import sys
import traceback
import time
from pathlib import Path
from PySide6.QtCore import QThread, Signal
import config
from modulo1_deteccion import DetectorYOLO
from modulo2_procesamiento import procesar_imagen
from modulo3_organizacion import (
    clasificar_escena,
    crear_estructura_directorios,
    guardar_imagen_original,
    guardar_insumos_objeto,
    generar_reporte,
)
from main import listar_imagenes, validar_rutas

class PipelineWorker(QThread):
    # progress: porcentaje (0-100)
    progress = Signal(int)
    # log: mensaje a imprimir en consola
    log = Signal(str)
    # image_processed: ruta a la imagen original, categoría, num_objetos, metadatos_lista
    image_processed = Signal(str, str, int, dict)
    # module_changed: modulo_id (1, 2, 3), estado ("waiting", "processing", "completed")
    module_changed = Signal(int, str)
    # status: estado general (imagen actual, total)
    status = Signal(int, int, float, float) # current, total, elapsed, remaining
    # finished: ruta_reporte
    finished = Signal(str)
    # error: mensaje de error
    error = Signal(str)

    def __init__(self, input_dir: str, output_dir: str, formato_reporte: str = "json"):
        super().__init__()
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.formato_reporte = formato_reporte
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            self.module_changed.emit(1, "processing")
            self.module_changed.emit(2, "waiting")
            self.module_changed.emit(3, "waiting")
            
            self.log.emit("Validando rutas de entrada y salida...")
            validar_rutas(self.input_dir, self.output_dir)
            imagenes = listar_imagenes(self.input_dir)
            
            if not imagenes:
                self.error.emit(f"No se encontraron imágenes en {self.input_dir}")
                return

            self.log.emit(f"Se encontraron {len(imagenes)} imágenes. Cargando YOLOv8...")
            detector = DetectorYOLO()
            # Cargar modelo explícitamente en el hilo secundario
            detector._cargar_modelo()
            
            self.module_changed.emit(1, "completed")
            self.module_changed.emit(2, "processing")
            
            rutas_estructura = crear_estructura_directorios(self.output_dir)
            registros = []
            inicio = time.time()
            total_imgs = len(imagenes)

            for idx, ruta_imagen in enumerate(imagenes, start=1):
                if self._is_cancelled:
                    self.log.emit("Procesamiento cancelado por el usuario.")
                    return

                nombre_base = ruta_imagen.stem
                self.log.emit(f"[{idx}/{total_imgs}] Procesando {ruta_imagen.name}")
                
                try:
                    # Módulo 1: Detección
                    self.module_changed.emit(1, "processing")
                    resultado_deteccion = detector.detectar(ruta_imagen)
                    categoria = clasificar_escena(resultado_deteccion.clases_detectadas)
                    
                    # Guardar imagen original
                    self.module_changed.emit(3, "processing")
                    rutas_bases = guardar_imagen_original(
                        rutas_estructura, categoria, nombre_base,
                        resultado_deteccion.imagen, resultado_deteccion.imagen_ploteada, self.output_dir
                    )

                    # Módulo 2: Procesamiento
                    self.module_changed.emit(2, "processing")
                    objetos_procesados = []
                    rutas_generadas = {**rutas_bases, "objetos": []}

                    if not resultado_deteccion.objetos:
                        insumos, metadatos = procesar_imagen(resultado_deteccion.imagen)
                        rutas_obj = guardar_insumos_objeto(
                            rutas_estructura, categoria, nombre_base, "full",
                            insumos, self.output_dir
                        )
                        rutas_generadas["objetos"].append(rutas_obj)
                        objetos_procesados.append({
                            "clase": "imagen_completa",
                            "color_dominante_rgb": metadatos.color_dominante_rgb,
                            "densidad_bordes": metadatos.densidad_bordes,
                            "energia_textura": metadatos.energia_textura,
                            "contraste_textura": metadatos.contraste_textura,
                        })
                    else:
                        for i, obj in enumerate(resultado_deteccion.objetos):
                            insumos, metadatos = procesar_imagen(obj.recorte, obj.mascara)
                            rutas_obj = guardar_insumos_objeto(
                                rutas_estructura, categoria, nombre_base, f"obj{i}",
                                insumos, self.output_dir
                            )
                            rutas_generadas["objetos"].append(rutas_obj)
                            objetos_procesados.append({
                                "clase": obj.clase,
                                "color_dominante_rgb": metadatos.color_dominante_rgb,
                                "densidad_bordes": metadatos.densidad_bordes,
                                "energia_textura": metadatos.energia_textura,
                                "contraste_textura": metadatos.contraste_textura,
                            })

                    registro_img = {
                        "nombre_original": ruta_imagen.name,
                        "categoria": categoria,
                        "clases_detectadas": sorted(resultado_deteccion.clases_detectadas),
                        "num_objetos_detectados": len(resultado_deteccion.objetos),
                        "objetos_procesados": objetos_procesados,
                        "rutas_generadas": rutas_generadas,
                    }
                    registros.append(registro_img)

                    # Emitir preview de la imagen procesada
                    # Tomar la ruta de la original copiada para mostrarla
                    ruta_guardada_completa = str(self.output_dir / rutas_bases["original"])
                    self.image_processed.emit(
                        ruta_guardada_completa,
                        categoria,
                        len(resultado_deteccion.objetos),
                        objetos_procesados[0] if objetos_procesados else {}
                    )

                except Exception as exc:
                    self.log.emit(f"Error procesando {ruta_imagen.name}: {str(exc)}")
                    traceback.print_exc()

                # Tiempos y Progreso
                transcurrido = time.time() - inicio
                avg_time = transcurrido / idx
                restante = avg_time * (total_imgs - idx)
                progreso_pct = int((idx / total_imgs) * 100)
                
                self.progress.emit(progreso_pct)
                self.status.emit(idx, total_imgs, transcurrido, restante)

            # Finalizar Módulo 3: Reporte
            self.module_changed.emit(3, "processing")
            self.log.emit("Generando reporte final...")
            tiempo_total = time.time() - inicio
            ruta_reporte = generar_reporte(
                registros, self.output_dir, formato=self.formato_reporte, tiempo_total_seg=tiempo_total
            )
            
            self.module_changed.emit(1, "completed")
            self.module_changed.emit(2, "completed")
            self.module_changed.emit(3, "completed")
            self.finished.emit(str(ruta_reporte))

        except Exception as exc:
            self.error.emit(f"Falla crítica en el pipeline: {str(exc)}")
            traceback.print_exc()
