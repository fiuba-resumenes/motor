#!/usr/bin/env python3
"""Verifica que un pase de acentuacion no haya alterado nada mas que las tildes.

Uso: python3 -m motor_apuntes.herramientas.verificar_tildes <backup_dir> <archivo.html> [...]

Invariante: quitarle los acentos al archivo nuevo debe reproducir exactamente el
original (que ya venia sin acentos). Ademas ids, hrefs y bloques de codigo tienen
que quedar intactos.
"""
import re
import sys
import unicodedata
from pathlib import Path

MAP = str.maketrans("áéíóúÁÉÍÓÚüÜñÑ", "aeiouAEIOUuUnN")


def desacentuar(s: str) -> str:
    return s.translate(MAP)


def ids_y_hrefs(s: str):
    return (re.findall(r'\sid="([^"]+)"', s),
            re.findall(r'href="([^"]+)"', s),
            re.findall(r'<pre><code[^>]*>(.*?)</code></pre>', s, re.S))


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__.strip().splitlines()[2])
        print("\nEjemplo: verificar_tildes.py /tmp/backup-fragmentos redes/*.html")
        return 2
    backup = Path(sys.argv[1])
    if not backup.is_dir():
        print(f"!! {backup} no es un directorio de backup")
        return 2
    fallas = 0
    for arg in sys.argv[2:]:
        nuevo_p = Path(arg)
        viejo_p = backup / nuevo_p.name
        if not viejo_p.exists():
            print(f"!! {nuevo_p.name}: sin backup para comparar")
            fallas += 1
            continue
        nuevo = nuevo_p.read_text(encoding="utf-8")
        viejo = viejo_p.read_text(encoding="utf-8")

        prob = []
        # Se normalizan los dos lados igual: agregar cualquier diacritico
        # (tilde, ñ, dieresis) esta permitido, cualquier otro cambio no.
        plano, base = desacentuar(nuevo), desacentuar(viejo)
        if plano != base:
            n = min(len(plano), len(base))
            i = next((k for k in range(n) if plano[k] != base[k]), n)
            prob.append("el texto cambio mas alla de los diacriticos; primera "
                        f"divergencia en offset {i}:\n"
                        f"        original: ...{base[max(0,i-60):i+60]!r}\n"
                        f"        nuevo:    ...{plano[max(0,i-60):i+60]!r}")

        iv, hv, cv = ids_y_hrefs(viejo)
        inu, hnu, cnu = ids_y_hrefs(nuevo)
        if iv != inu:
            prob.append(f"ids modificados: {set(iv) ^ set(inu)}")
        if hv != hnu:
            prob.append(f"hrefs modificados: {set(hv) ^ set(hnu)}")
        if cv != cnu:
            prob.append(f"{sum(1 for a, b in zip(cv, cnu) if a != b)} bloque(s) "
                        "de codigo modificados")

        acentos = sum(nuevo.count(c) for c in "áéíóúÁÉÍÓÚ")
        if prob:
            fallas += 1
            print(f"!! {nuevo_p.name}  (+{acentos} acentos)")
            for p in prob:
                print("      -", p)
        else:
            print(f"OK {nuevo_p.name}  (+{acentos} acentos, nada mas cambio)")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
