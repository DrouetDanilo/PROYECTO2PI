"""
main.py
-------
Clasificador y Organizador Automático de Fotografías por Tipo de Escena.

Orquesta el flujo completo en una sola ejecución (dentro del alcance del
proyecto), integrando:

  Módulo 1 -> Detección de objetos (YOLO)
  Módulo 2 -> Procesamiento y análisis visual (OpenCV + K-Means + GLCM)
  Módulo 3 -> Organización de archivos y reporte final

Uso:
    python main.py --input ./mis_fotos --output ./Datasets/Resultados_DIP --formato json
"""

import argparse
import sys
import time
from pathlib import Path

import config
from modulo1_deteccion import DetectorYOLO
from modulo2_procesamiento import procesar_imagen
from modulo3_organizacion import (
    clasificar_escena,
    crear_estructura_directorios,
    generar_reporte,
    guardar_imagen_original,
    guardar_insumos_objeto,
    limpiar_directorio,
)


def listar_imagenes(input_dir: Path):
    """RF-01: recolecta todas las imágenes válidas de la carpeta de entrada."""
    return sorted(
        p for p in input_dir.rglob("*")
        if p.suffix.lower() in config.VALID_EXTENSIONS and p.is_file()
    )


def validar_rutas(input_dir: Path, output_dir: Path):
    if not input_dir.exists() or not input_dir.is_dir():
        raise NotADirectoryError(f"La carpeta de entrada no existe o no es válida: {input_dir}")
    config.ensure_dir(output_dir)


def ejecutar_pipeline(input_dir: str, output_dir: str, formato_reporte: str = config.DEFAULT_REPORT_FORMAT):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    validar_rutas(input_dir, output_dir)
    imagenes = listar_imagenes(input_dir)

    if not imagenes:
        print(f"[AVISO] No se encontraron imágenes ({', '.join(config.VALID_EXTENSIONS)}) en {input_dir}")
        return

    print(f"[INFO] {len(imagenes)} imágenes encontradas. Iniciando pipeline...\n")

    detector = DetectorYOLO()
    rutas_estructura = crear_estructura_directorios(output_dir)

    registros = []
    inicio = time.time()

    for idx, ruta_imagen in enumerate(imagenes, start=1):
        nombre_base = ruta_imagen.stem
        print(f"[{idx}/{len(imagenes)}] Procesando {ruta_imagen.name}...")

        try:
            # ---- Módulo 1: Detección ----
            resultado_deteccion = detector.detectar(ruta_imagen)
            categoria = clasificar_escena(resultado_deteccion.clases_detectadas)

            # ---- Módulo 3: Guardar la imagen original (y ploteada) primero ----
            rutas_bases = guardar_imagen_original(
                rutas_estructura, categoria, nombre_base,
                resultado_deteccion.imagen, resultado_deteccion.imagen_ploteada, output_dir
            )

            # ---- Módulo 2 y 3: Procesamiento y análisis visual por objeto ----
            objetos_procesados = []
            rutas_generadas = {**rutas_bases, "objetos": []}

            if not resultado_deteccion.objetos:
                # Si no hay objetos, procesamos la imagen completa como respaldo
                insumos, metadatos = procesar_imagen(resultado_deteccion.imagen)
                rutas_obj = guardar_insumos_objeto(
                    rutas_estructura, categoria, nombre_base, "full",
                    insumos, output_dir
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
                    insumos, metadatos = procesar_imagen(obj.recorte)
                    rutas_obj = guardar_insumos_objeto(
                        rutas_estructura, categoria, nombre_base, f"obj{i}",
                        insumos, output_dir
                    )
                    rutas_generadas["objetos"].append(rutas_obj)
                    objetos_procesados.append({
                        "clase": "objeto_detectado",
                        "color_dominante_rgb": metadatos.color_dominante_rgb,
                        "densidad_bordes": metadatos.densidad_bordes,
                        "energia_textura": metadatos.energia_textura,
                        "contraste_textura": metadatos.contraste_textura,
                    })

            registros.append({
                "nombre_original": ruta_imagen.name,
                "categoria": categoria,
                "clases_detectadas": sorted(resultado_deteccion.clases_detectadas),
                "num_objetos_detectados": len(resultado_deteccion.objetos),
                "objetos_procesados": objetos_procesados,
                "rutas_generadas": rutas_generadas,
            })

            print(f"    -> Categoría: {categoria} | Objetos: {len(resultado_deteccion.objetos)}")
            for obj in objetos_procesados:
                print(f"       - Objeto | RGB: {obj['color_dominante_rgb']} | Bordes: {obj['densidad_bordes']}")

        except Exception as exc:
            print(f"    [ERROR] No se pudo procesar {ruta_imagen.name}: {exc}")

    tiempo_total = time.time() - inicio

    ruta_reporte = generar_reporte(
        registros, output_dir, formato=formato_reporte, tiempo_total_seg=tiempo_total
    )

    print("\n[COMPLETADO] Procesamiento finalizado.")
    print(f"  Imágenes procesadas: {len(registros)}/{len(imagenes)}")
    print(f"  Tiempo total: {tiempo_total:.2f} s")
    print(f"  Reporte generado en: {ruta_reporte}")
    print(f"  Resultados organizados en: {output_dir.resolve()}")


def main():
    parser = argparse.ArgumentParser(
        description="Clasificador y Organizador Automático de Fotografías por Tipo de Escena."
    )
    parser.add_argument("--input", "-i", default=config.DEFAULT_INPUT_DIR,
                         help="Carpeta de entrada con las imágenes a procesar.")
    parser.add_argument("--output", "-o", default=config.DEFAULT_OUTPUT_DIR,
                         help="Carpeta de salida donde se guardarán los resultados.")
    parser.add_argument("--formato", "-f", default=config.DEFAULT_REPORT_FORMAT,
                         choices=config.REPORT_FORMATS,
                         help="Formato del reporte final: txt, json o pdf.")
    parser.add_argument("--gui", action="store_true", help="Lanzar la interfaz gráfica de usuario PySide6.")
    args = parser.parse_args()

    if args.gui or (len(sys.argv) == 1):
        try:
            from gui.main_window import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"[ERROR] No se pudo cargar la interfaz gráfica: {e}")
            sys.exit(1)
        return

    try:
        ejecutar_pipeline(args.input, args.output, args.formato)
    except (NotADirectoryError, FileNotFoundError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[CANCELADO] Procesamiento interrumpido por el usuario.")
        sys.exit(1)


if __name__ == "__main__":
    main()