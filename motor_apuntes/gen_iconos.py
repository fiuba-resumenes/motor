"""Rasteriza los iconos PNG de la PWA de una materia.

armar.py genera en cada build todo lo que es texto (icon.svg, manifest,
sw.js), pero los PNG que piden iOS y el instalador de Chrome necesitan
ImageMagick, y el build no debe depender de herramientas externas: se
rasterizan aca UNA vez y van commiteados (armar.py solo valida que existan).
Correr de nuevo solo si cambia favicon_hex de la materia o el glifo.
"""
import subprocess
from pathlib import Path

from .armar import icono_svg

# apple-touch-icon: iOS no aplica mascara, pero el fondo a sangre completa
# del icono ya lo deja opaco y cuadrado, que es lo que espera.
TAMANOS = {"icon-192.png": 192, "icon-512.png": 512, "apple-touch-icon.png": 180}


def generar(cfg: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    svg = out_dir / "icon.svg"
    svg.write_text(icono_svg(cfg["favicon_hex"]), encoding="utf-8")
    for nombre, lado in TAMANOS.items():
        # densidad para que el SVG (viewBox de 64 a 96 dpi) se renderice ya
        # al tamano final, sin reescalar un raster chico
        subprocess.run(
            ["magick", "-background", "none",
             "-density", str(lado * 96 // 64), str(svg),
             "-resize", f"{lado}x{lado}", str(out_dir / nombre)],
            check=True)
        print(f"{nombre}: {lado}x{lado}")
