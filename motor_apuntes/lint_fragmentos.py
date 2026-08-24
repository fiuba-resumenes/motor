#!/usr/bin/env python3
"""Valida fragmentos de una materia antes de ensamblar.

Chequea lo que el contrato pide y lo que ya rompio alguna vez:
tags balanceados, tokens de color permitidos, < y > escapados dentro de
pre/code, SVG con viewBox y aria-label, figuras con figcaption, ids unicos
entre fragmentos, guiones largos y middle dots, y texto sin tildes.

Uso: python3 -m motor_apuntes.lint_fragmentos <archivo.html o carpeta> ...
No hay default: cada repo de materia pasa su propia carpeta de fragmentos
(no hay una convencion de nombre fija para esa carpeta, la decide el repo).
"""
import html.parser
import re
import sys
import unicodedata
from pathlib import Path

# Los unicos tokens de color que el motor define como alias (ver CSS_EXTRA
# en armar.py). --acc3 (calido) y --acc4 (riesgo) son series extra para
# graficos con mas de dos curvas; --grid es la reticula tenue de los graficos.
TOKENS_OK = {"--acc", "--acc2", "--acc3", "--acc4", "--linea", "--grid"}

# Void y elementos SVG que no cierran.
VACIOS = {
    "br", "img", "hr", "input", "meta", "link", "source", "col",
    "path", "rect", "line", "circle", "ellipse", "polygon", "polyline",
    "use", "stop", "image",
}

CLASES_OK = {
    "def", "idea", "ej", "warn", "examen", "mas", "preg", "diag",
    "nota", "ref", "glo", "unidad", "intro", "tablewrap",
    # formula: recuadro para formulas sueltas, parte del contrato.
    "formula",
    # riesgo: consecuencia grave o irreversible, mas fuerte que warn.
    "riesgo",
}

# Palabras que en un apunte en espanol van con tilde y suelen aparecer sin
# ella cuando un agente "se cuida" de los caracteres especiales.
SIN_TILDE = re.compile(
    r"\b(comunicacion|funcion|informacion|aplicacion|version|particion|"
    r"replicacion|operacion|transaccion|coordinacion|sincronizacion|"
    r"ejecucion|conexion|tambien|ademas|asincronico|sincronico|"
    r"parametro|deteccion|eleccion|seccion|division|difusion|"
    r"topologia|multiples|unico|unica|ultimo|jerarquica|jerarquico|"
    r"maximo|minimo|numero|codigo|metodo|practica|teorico|patron|"
    r"anonima|anonimo|heterogeneos|heterogeneo|sesion|peticion|"
    r"resolucion|precision|decision|revision|emision|transmision)\b",
    re.IGNORECASE,
)

# El texto de los SVG es el punto ciego historico: acentuar.py salteaba los
# bloques <svg>, asi que las etiquetas de los diagramas quedaron sin tildes.
# Se revisan aparte, salteando lo que es un identificador y no prosa.
NO_ES_PROSA = re.compile(r"^(region|numero)$", re.IGNORECASE)

GENERADOS = {"autoevaluacion.html", "glosario.html"}


class Balance(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.pila = []
        self.errores = []

    def handle_starttag(self, tag, attrs):
        if tag not in VACIOS:
            self.pila.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if self.pila and self.pila[-1][0] == tag:
            self.pila.pop()
        else:
            abiertos = [t for t, _ in self.pila]
            if tag in abiertos:
                i = len(abiertos) - 1 - abiertos[::-1].index(tag)
                sin_cerrar = [t for t, _ in self.pila[i + 1:]]
                self.errores.append(
                    f"linea {self.getpos()[0]}: </{tag}> con {sin_cerrar} sin cerrar")
                del self.pila[i:]
            else:
                self.errores.append(
                    f"linea {self.getpos()[0]}: </{tag}> sin apertura")


def sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def revisar(path: Path) -> list:
    txt = path.read_text(encoding="utf-8")
    fallas = []

    b = Balance()
    b.feed(txt)
    fallas += b.errores
    if b.pila:
        fallas.append(f"sin cerrar al final: {[(t, l) for t, l in b.pila]}")

    # Tokens de color: solo los alias del contrato.
    for tok in set(re.findall(r"var\(\s*(--[a-z0-9-]+)", txt)):
        if tok not in TOKENS_OK:
            fallas.append(f"token de color no permitido: var({tok})")

    # Colores hardcodeados dentro de SVG.
    for svg in re.findall(r"<svg.*?</svg>", txt, re.S):
        for m in re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{3,8}|rgb[^"]*)"', svg):
            fallas.append(f"color hardcodeado en SVG: {m}")

    # SVG accesible y figuras con epigrafe.
    for m in re.finditer(r"<svg([^>]*)>", txt):
        at = m.group(1)
        linea = txt[:m.start()].count("\n") + 1
        if "viewBox" not in at:
            fallas.append(f"linea {linea}: <svg> sin viewBox")
        if "aria-label" not in at and "aria-labelledby" not in at:
            fallas.append(f"linea {linea}: <svg> sin aria-label")
    for m in re.finditer(r'<figure class="diag">(.*?)</figure>', txt, re.S):
        if "<figcaption" not in m.group(1):
            linea = txt[:m.start()].count("\n") + 1
            fallas.append(f"linea {linea}: figure.diag sin figcaption")

    # < y > crudos dentro de pre/code: rompen todo lo que sigue.
    for m in re.finditer(r"<pre><code>(.*?)</code></pre>", txt, re.S):
        cuerpo = m.group(1)
        linea = txt[:m.start()].count("\n") + 1
        crudo = re.findall(r"<(?!/?(?:code|pre)\b)[^\s=]", cuerpo)
        if crudo:
            fallas.append(f"linea {linea}: '<' sin escapar dentro de pre/code")

    # Clases desconocidas: delatan un typo que deja el bloque sin estilo.
    for c in re.findall(r'class="([^"]+)"', txt):
        for parte in c.split():
            if parte not in CLASES_OK:
                fallas.append(f"clase desconocida: {parte}")

    # Reglas de estilo del usuario.
    for mal, nombre in ((chr(0x2014), "guion largo"),
                        (chr(0x2013), "guion medio"),
                        (chr(0xB7), "middle dot")):
        if mal in txt:
            n = txt.count(mal)
            fallas.append(f"{nombre} usado {n} vez/veces")

    # Texto visible sin tildes (ignora tags, code, pre, svg y formulas: una
    # formula usa los nombres de sus variables/metricas tal cual, en ingles
    # si asi las nombra la fuente, no es prosa en espanol).
    visible = re.sub(r"<(pre|code|svg)\b.*?</\1>", " ", txt, flags=re.S)
    visible = re.sub(r'<(span|div) class="formula">.*?</\1>', " ", visible, flags=re.S)
    visible = re.sub(r"<[^>]+>", " ", visible)
    faltantes = {}
    for m in SIN_TILDE.finditer(visible):
        pal = m.group(0).lower()
        faltantes[pal] = faltantes.get(pal, 0) + 1
    if faltantes:
        top = ", ".join(f"{k} x{v}" for k, v in sorted(faltantes.items())[:8])
        fallas.append(f"palabras sin tilde: {top}")

    # Etiquetas de los diagramas: se saltea lo que es identificador, no prosa
    # (un nombre de mensaje como eleccion(45) va sin tilde a proposito).
    en_svg = {}
    for svg in re.findall(r"<svg\b.*?</svg>", txt, re.S):
        for nodo in re.findall(r">([^<>]+)<", svg):
            for m in SIN_TILDE.finditer(nodo):
                pal = m.group(0)
                if NO_ES_PROSA.match(pal):
                    continue
                if nodo[m.end():m.end() + 1] == "(":
                    continue
                en_svg[pal.lower()] = en_svg.get(pal.lower(), 0) + 1
    if en_svg:
        top = ", ".join(f"{k} x{v}" for k, v in sorted(en_svg.items())[:8])
        fallas.append(f"palabras sin tilde en etiquetas de SVG: {top}")

    return fallas


def _archivos(rutas: list) -> list:
    if not rutas:
        raise SystemExit("uso: lint_fragmentos.py <archivo.html o carpeta> ...")
    out = []
    for r in rutas:
        p = Path(r)
        if p.is_dir():
            out += [f for f in sorted(p.glob("*.html")) if f.name not in GENERADOS]
        else:
            out.append(p)
    return out


def main(argv):
    archivos = _archivos(argv)
    total = 0
    ids = {}
    for p in archivos:
        fallas = revisar(p)
        for i in re.findall(r'\sid="([^"]+)"', p.read_text(encoding="utf-8")):
            ids.setdefault(i, []).append(p.name)
        if fallas:
            total += len(fallas)
            print(f"\n{p.name}")
            for f in fallas:
                print(f"  !! {f}")
        else:
            print(f"{p.name}: ok")

    dup = {i: v for i, v in ids.items() if len(v) > 1}
    if dup:
        total += len(dup)
        print("\nids repetidos entre fragmentos:")
        for i, v in sorted(dup.items()):
            print(f"  !! {i} en {v}")

    print(f"\n{total} hallazgo(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
