"""
modulo3_organizacion.py
------------------------
MÓDULO #3: ORGANIZACIÓN DE ARCHIVOS

Entrada:  Insumos visuales procesados, metadatos y arreglos consolidados.
Proceso:  Análisis lógico de propiedades/metadatos para mapear dinámicamente
          una estructura jerárquica física de almacenamiento.
Salida:   Rutas físicas creadas en el directorio local, estructura jerárquica
          de carpetas y reporte analítico final (TXT, JSON o PDF).

RF-06, RF-07, RNF-01.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

import cv2

import config


def clasificar_escena(clases_detectadas: set) -> str:
    """
    Determina la categoría de escena de una imagen a partir de las clases
    detectadas por YOLO en el Módulo 1, siguiendo config.SCENE_PRIORITY.
    Si no hay coincidencias, se asigna la categoría por defecto ("Paisajes").
    """
    for categoria in config.SCENE_PRIORITY:
        clases_categoria = config.SCENE_CATEGORY_MAP[categoria]
        if clases_detectadas & clases_categoria:
            return categoria
    return config.DEFAULT_SCENE_CATEGORY


def crear_estructura_directorios(output_dir: Path) -> dict:
    """
    Crea la estructura jerárquica de carpetas (RF-06):
      /originales, /bordes_crudos, /bordes_procesados, /mascaras, /recortes
    y dentro de cada una, una subcarpeta por categoría de escena.
    """
    rutas = {}
    for clave, nombre in config.SUBFOLDERS.items():
        base = output_dir / nombre
        for categoria in config.ALL_CATEGORIES:
            (base / categoria).mkdir(parents=True, exist_ok=True)
        rutas[clave] = base
    return rutas


def guardar_imagen_original(rutas: dict, categoria: str, nombre_base: str,
                             imagen_original, imagen_ploteada, output_dir: Path) -> dict:
    """Guarda la imagen original completa y su versión ploteada (segmentada general)."""
    rutas_generadas = {}
    destino_original = rutas["originales"] / categoria / f"{nombre_base}.jpg"
    cv2.imwrite(str(destino_original), imagen_original)
    rutas_generadas["original"] = str(destino_original.relative_to(output_dir))
    
    if imagen_ploteada is not None:
        destino_ploteada = rutas["originales"] / categoria / f"{nombre_base}_segmentada_general.jpg"
        cv2.imwrite(str(destino_ploteada), imagen_ploteada)
        rutas_generadas["segmentada_general"] = str(destino_ploteada.relative_to(output_dir))
        
    return rutas_generadas


def guardar_insumos_objeto(rutas: dict, categoria: str, nombre_base: str, obj_id: str,
                           insumos, output_dir: Path) -> dict:
    """
    Persiste en disco los 4 insumos visuales de un objeto específico dentro de
    la categoría de escena correspondiente.
    """
    rutas_generadas = {}
    prefijo = f"{nombre_base}_{obj_id}"

    destino_crudos = rutas["bordes_crudos"] / categoria / f"{prefijo}_bordes_crudos.jpg"
    cv2.imwrite(str(destino_crudos), insumos.bordes_crudos)
    rutas_generadas["bordes_crudos"] = str(destino_crudos.relative_to(output_dir))

    destino_filtrados = rutas["bordes_procesados"] / categoria / f"{prefijo}_bordes_filtrados.jpg"
    cv2.imwrite(str(destino_filtrados), insumos.bordes_filtrados)
    rutas_generadas["bordes_filtrados"] = str(destino_filtrados.relative_to(output_dir))

    destino_mascara = rutas["mascaras"] / categoria / f"{prefijo}_mascara.jpg"
    cv2.imwrite(str(destino_mascara), insumos.mascara_binaria)
    rutas_generadas["mascara"] = str(destino_mascara.relative_to(output_dir))

    destino_recorte = rutas["recortes"] / categoria / f"{prefijo}_segmentado.jpg"
    cv2.imwrite(str(destino_recorte), insumos.objeto_segmentado)
    rutas_generadas["objeto_segmentado"] = str(destino_recorte.relative_to(output_dir))

    return rutas_generadas


def generar_reporte(registros: List[dict], output_dir: Path,
                     formato: str = config.DEFAULT_REPORT_FORMAT,
                     tiempo_total_seg: float = 0.0) -> Path:
    """
    Genera el reporte analítico final (RF-07) con estadísticas generales del
    procesamiento y la metadata recolectada, en formato TXT, JSON o PDF.
    """
    conteo_categorias = {cat: 0 for cat in config.ALL_CATEGORIES}
    for r in registros:
        conteo_categorias[r["categoria"]] += 1

    resumen = {
        "fecha_generacion": datetime.now().isoformat(timespec="seconds"),
        "total_imagenes_procesadas": len(registros),
        "categorias_generadas": len([c for c, n in conteo_categorias.items() if n > 0]),
        "conteo_por_categoria": conteo_categorias,
        "tiempo_total_segundos": round(tiempo_total_seg, 2),
        "detalle": registros,
    }

    ruta_reporte = output_dir / f"{config.REPORT_FILENAME_BASE}.{formato}"

    if formato == "json":
        with open(ruta_reporte, "w", encoding="utf-8") as f:
            json.dump(resumen, f, indent=2, ensure_ascii=False)

    elif formato == "txt":
        with open(ruta_reporte, "w", encoding="utf-8") as f:
            f.write("REPORTE FINAL - Clasificador Automático de Fotografías\n")
            f.write("=" * 60 + "\n")
            f.write(f"Fecha de generación: {resumen['fecha_generacion']}\n")
            f.write(f"Total de imágenes procesadas: {resumen['total_imagenes_procesadas']}\n")
            f.write(f"Categorías generadas: {resumen['categorias_generadas']}\n")
            f.write(f"Tiempo total: {resumen['tiempo_total_segundos']} s\n\n")
            f.write("Conteo por categoría:\n")
            for cat, n in conteo_categorias.items():
                f.write(f"  - {cat}: {n} fotos\n")
            f.write("\nDetalle por imagen:\n")
            for r in registros:
                f.write(f"  * {r['nombre_original']} -> {r['categoria']} ({r['num_objetos_detectados']} objetos)\n")
                for obj in r.get('objetos_procesados', []):
                    f.write(f"      - {obj['clase']} | RGB: {obj['color_dominante_rgb']} | Bordes: {obj['densidad_bordes']}\n")

    elif formato == "pdf":
        _generar_reporte_pdf(resumen, ruta_reporte)

    else:
        raise ValueError(f"Formato de reporte no soportado: {formato}")

    return ruta_reporte


def _generar_reporte_pdf(resumen: dict, ruta_reporte: Path):
    """Genera una versión PDF simple del reporte usando reportlab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise ImportError(
            "El paquete 'reportlab' no está instalado. Ejecuta: pip install reportlab"
        ) from exc

    c = canvas.Canvas(str(ruta_reporte), pagesize=letter)
    ancho, alto = letter
    y = alto - 50

    def linea(texto, salto=16, tam=11):
        nonlocal y
        c.setFont("Helvetica", tam)
        c.drawString(50, y, texto)
        y -= salto
        if y < 50:
            c.showPage()
            y = alto - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Reporte Final - Clasificador Automático de Fotografías")
    y -= 30

    linea(f"Fecha de generación: {resumen['fecha_generacion']}")
    linea(f"Total de imágenes procesadas: {resumen['total_imagenes_procesadas']}")
    linea(f"Categorías generadas: {resumen['categorias_generadas']}")
    linea(f"Tiempo total: {resumen['tiempo_total_segundos']} s")
    linea("")
    linea("Conteo por categoría:", tam=12)
    for cat, n in resumen["conteo_por_categoria"].items():
        linea(f"  - {cat}: {n} fotos")

    linea("")
    linea("Detalle por imagen:", tam=12)
    for r in resumen["detalle"]:
        linea(f"  * {r['nombre_original']} -> {r['categoria']}")

    c.save()


def limpiar_directorio(output_dir: Path):
    """Elimina resultados parciales (usado si el usuario cancela el proceso)."""
    if output_dir.exists():
        shutil.rmtree(output_dir)