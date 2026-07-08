"""
modulo1_deteccion.py
---------------------
MÓDULO #1: DETECCIÓN

Entrada:  Matrices de píxeles de las imágenes crudas (RF-01, RF-02)
Proceso:  Inferencia visual mediante el modelo preentrenado YOLO. Localiza
          elementos clave de interés (personas, animales, comida, objetos, etc.)
Salida:   Tensores numéricos (bounding boxes) + recortes vectoriales/rasterizados
          de los objetos principales.

RF-02: El sistema debe invocar el modelo preentrenado YOLO para identificar
       los objetos principales y extraer sus coordenadas (bounding boxes)
       sin intervención manual.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import numpy as np

import config


@dataclass
class DeteccionObjeto:
    """Representa un objeto detectado dentro de una imagen."""
    clase: str
    confianza: float
    bbox: tuple  # (x1, y1, x2, y2) en píxeles
    recorte: np.ndarray = field(repr=False)  # matriz de píxeles del recorte


@dataclass
class ResultadoDeteccion:
    """Resultado completo del Módulo 1 para una imagen."""
    ruta_imagen: Path
    imagen: np.ndarray = field(repr=False)
    imagen_ploteada: np.ndarray = field(repr=False, default=None)
    objetos: List[DeteccionObjeto] = field(default_factory=list)

    @property
    def clases_detectadas(self):
        return {obj.clase for obj in self.objetos}


class DetectorYOLO:
    """
    Encapsula la carga del modelo YOLO (Ultralytics) y la inferencia sobre
    imágenes individuales. Se carga una sola vez y se reutiliza en todo el
    pipeline (RNF-03: eficiencia en procesamiento).
    """

    def __init__(self, model_name: str = config.YOLO_MODEL_NAME,
                 conf_threshold: float = config.YOLO_CONF_THRESHOLD):
        self.model_name = model_name
        self.conf_threshold = conf_threshold
        self._model = None

    def _cargar_modelo(self):
        if self._model is None:
            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise ImportError(
                    "El paquete 'ultralytics' no está instalado. "
                    "Ejecuta: pip install ultralytics"
                ) from exc
            self._model = YOLO(self.model_name)
        return self._model

    def detectar(self, ruta_imagen: Path) -> ResultadoDeteccion:
        """
        Ejecuta la inferencia YOLO sobre una imagen y retorna el resultado
        estructurado con los bounding boxes y los recortes de cada objeto.
        """
        import cv2

        model = self._cargar_modelo()
        imagen = cv2.imread(str(ruta_imagen))
        if imagen is None:
            raise FileNotFoundError(f"No se pudo leer la imagen: {ruta_imagen}")

        resultados = model.predict(
            source=str(ruta_imagen),
            conf=self.conf_threshold,
            verbose=False,
        )

        objetos = []
        imagen_ploteada = None
        
        if resultados:
            r = resultados[0]
            imagen_ploteada = r.plot(labels=False)  # Genera máscaras de colores pero sin textos
            
            nombres = r.names
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                x1, y1 = max(x1, 0), max(y1, 0)
                x2 = min(x2, imagen.shape[1])
                y2 = min(y2, imagen.shape[0])
                recorte = imagen[y1:y2, x1:x2].copy()
                objetos.append(
                    DeteccionObjeto(
                        clase=nombres.get(cls_id, str(cls_id)),
                        confianza=conf,
                        bbox=(x1, y1, x2, y2),
                        recorte=recorte,
                    )
                )

        return ResultadoDeteccion(ruta_imagen=ruta_imagen, imagen=imagen, imagen_ploteada=imagen_ploteada, objetos=objetos)