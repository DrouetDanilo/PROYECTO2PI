"""
modulo1_deteccion.py
---------------------
MÓDULO #1: DETECCIÓN Y SEGMENTACIÓN (CORREGIDO)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
import config


@dataclass
class DeteccionObjeto:
    """Representa un objeto detectado y segmentado dentro de una imagen."""
    clase: str
    confianza: float
    bbox: tuple  # (x1, y1, x2, y2) en píxeles
    recorte: np.ndarray = field(repr=False)  # Subimagen rectangular con fondo
    mascara: Optional[np.ndarray] = field(default=None, repr=False)  # Máscara B/N (255=objeto, 0=fondo)


@dataclass
class ResultadoDeteccion:
    """Resultado completo del Módulo 1 para una imagen."""
    ruta_imagen: Path
    imagen: np.ndarray = field(repr=False)
    imagen_ploteada: Optional[np.ndarray] = field(repr=False, default=None)
    objetos: List[DeteccionObjeto] = field(default_factory=list)

    @property
    def clases_detectadas(self):
        return {obj.clase for obj in self.objetos}


class DetectorYOLO:
    """
    Encapsula la carga del modelo YOLO (Ultralytics) y la inferencia sobre
    imágenes individuales.
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
        Ejecuta la inferencia YOLO y retorna el resultado estructurado
        con máscaras binarias perfectamente alineadas.
        """
        model = self._cargar_modelo()
        imagen = cv2.imread(str(ruta_imagen))
        if imagen is None:
            raise FileNotFoundError(f"No se pudo leer la imagen: {ruta_imagen}")

        h_img, w_img = imagen.shape[:2]

        resultados = model.predict(
            source=imagen,
            conf=self.conf_threshold,
            imgsz=640,
            verbose=False,
        )

        objetos = []
        imagen_ploteada = None

        if resultados:
            r = resultados[0]
            imagen_ploteada = r.plot(labels=False)

            nombres = r.names
            
            # SOLUCIÓN: Obtener máscaras procesadas y escaladas a la imagen original por Ultralytics
            masks_np = None
            if r.masks is not None:
                # r.masks.xyn o r.masks.data procesados con la API de Ultralytics
                # Redimensionamos cada máscara individualmente con flags limpios
                masks_np = r.masks.data.cpu().numpy()

            for idx, box in enumerate(r.boxes):
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                
                # Ajustar coordenadas a límites reales de la imagen
                x1, y1 = max(x1, 0), max(y1, 0)
                x2, y2 = min(x2, w_img), min(y2, h_img)

                # 1. RECORTE RECTANGULAR PURO
                recorte_rectangulo = imagen[y1:y2, x1:x2].copy()
                h_crop, w_crop = recorte_rectangulo.shape[:2]

                if h_crop == 0 or w_crop == 0:
                    continue

                # 2. MÁSCARA BINARIA ALINEADA
                mascara_binaria = None
                if masks_np is not None and idx < len(masks_np):
                    # Redimensionar la máscara de baja resolución a la imagen original
                    single_mask = masks_np[idx]
                    mask_full = cv2.resize(
                        single_mask, 
                        (w_img, h_img), 
                        interpolation=cv2.INTER_CUBIC
                    )
                    
                    # Cortar la sub-máscara exacta para el Bounding Box
                    mask_crop = mask_full[y1:y2, x1:x2]
                    
                    # Umbralizado limpio y estricto a uint8 (255 objeto, 0 fondo)
                    mascara_binaria = np.where(mask_crop > 0.5, 255, 0).astype(np.uint8)

                objetos.append(
                    DeteccionObjeto(
                        clase=nombres.get(cls_id, str(cls_id)),
                        confianza=conf,
                        bbox=(x1, y1, x2, y2),
                        recorte=recorte_rectangulo,
                        mascara=mascara_binaria,
                    )
                )

        return ResultadoDeteccion(
            ruta_imagen=ruta_imagen,
            imagen=imagen,
            imagen_ploteada=imagen_ploteada,
            objetos=objetos
        )