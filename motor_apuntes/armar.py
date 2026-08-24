"""Arma el apunte de una materia sobre el shell compartido.

Motor generico: la identidad, la paleta y el indice de una materia salen de
su propia config (un dict, no un modulo compartido), y los fragmentos de un
directorio que el llamador indica. Este modulo no sabe nada de que materias
existen ni de donde vive cada repo: eso es responsabilidad del wrapper que
cada repo de materia trae (ver README del paquete).
"""
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

from . import autoria

BASE = Path(__file__).resolve().parent
SHELL = BASE / "shell.html"
# Modulos que se inyectan antes de </body>, en este orden.
MODULOS = [BASE / "sync.html", BASE / "imprimir.html"]

# vocabulario propio de los fragmentos -> callouts del shell
CLASES = {
    "def": "callout",
    "idea": "callout blue",
    "ej": "callout example",
    "warn": "callout warning",
    "examen": "callout exam",
    "riesgo": "callout danger",
}

CSS_EXTRA = """
    /* ---- agregados para estos apuntes ---- */
    .callout.example { border-color: var(--ok); background: var(--ok-bg); color: var(--ok); }
    .callout.exam { border-color: var(--exam); background: var(--exam-bg); color: var(--exam); }
    .callout > b:first-child, .callout > strong:first-child { color: inherit; }
    .callout.blue::before { content: "Intuición"; }
    .callout.example::before { content: "Ejemplo"; }
    .callout.warning::before { content: "Ojo"; }
    .callout.exam::before { content: "Tomado en finales"; }
    .callout.danger::before { content: "Riesgo"; }
    .callout.blue::before, .callout.example::before,
    .callout.warning::before, .callout.exam::before,
    .callout.danger::before {
      display: block;
      margin-bottom: 6px;
      font-size: 10px;
      font-weight: 800;
      letter-spacing: .1em;
      text-transform: uppercase;
      opacity: .85;
    }
    p.intro {
      margin: 0 0 26px;
      color: var(--muted);
      font-size: 18px;
      line-height: 1.6;
    }
    pre {
      margin: 16px 0 22px;
      padding: 16px 18px;
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--surface-2);
      font-size: 13.5px;
      line-height: 1.55;
    }
    pre code { font-size: inherit; }
    :not(pre) > code {
      padding: 1px 6px;
      border-radius: 6px;
      background: var(--surface-2);
    }
    figure.diag {
      margin: 22px 0;
      padding: 18px 16px 12px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--surface);
      text-align: center;
    }
    /* Alias que usan los SVG de los fragmentos y las figuras generadas (ver
       contrato-fragmento.md). --linea no apunta a --line: ese token es un
       borde decorativo de 1.2:1 y como trazo de diagrama no se veria. Las
       flechas necesitan --muted. --grid si es --line: las reticulas de los
       graficos tienen que ser mas tenues que los ejes. --acc3 y --acc4 son
       series extra para graficos con mas de dos curvas. */
    :root, html[data-theme="dark"] {
      --linea: var(--muted);
      --acc: var(--accent);
      --acc2: var(--blue);
      --acc3: var(--warm);
      --acc4: var(--danger);
      --grid: var(--line);
    }
    figure.diag svg { max-width: 100%; height: auto; color: var(--ink); }
    /* Los PNG importados (capturas de Notion) traen texto oscuro sobre fondo
       transparente: sin este fondo claro serian ilegibles en modo oscuro. */
    figure.diag img {
      display: block;
      box-sizing: border-box;
      max-width: 100%;
      height: auto;
      margin: 0 auto;
      padding: 10px;
      border-radius: 10px;
      background: #fff;
    }
    /* Leyenda de series de las figuras generadas (gen_figuras_*.py). */
    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 18px;
      justify-content: center;
      margin: 10px 0 2px;
      color: var(--muted);
      font-size: 12.5px;
    }
    .legend i {
      display: inline-block;
      width: 12px;
      height: 12px;
      margin-right: 6px;
      border-radius: 3px;
      vertical-align: -1px;
    }
    /* Tarjetas de elasticidad (figuras elast-*). */
    .elast-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(148px, 1fr));
      gap: 10px;
      margin: 16px 0 22px;
    }
    .elast-card {
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: var(--surface-2);
      text-align: center;
    }
    .elast-card svg { display: block; width: 100%; height: auto; margin-bottom: 8px; color: var(--ink); }
    .elast-card b { display: block; font-size: 12.5px; color: var(--accent-ink); line-height: 1.25; }
    .elast-card .ep { display: block; font-size: 17px; font-weight: 800; margin: 4px 0 2px; }
    .elast-card small { display: block; color: var(--muted); font-size: 11.5px; line-height: 1.35; }
    figure.diag figcaption {
      margin-top: 12px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
      text-align: left;
    }
    p.nota {
      margin: 14px 0;
      padding-left: 14px;
      border-left: 3px solid var(--line);
      color: var(--muted);
      font-size: 14.5px;
    }
    p.ref {
      margin: 14px 0 0;
      padding-top: 10px;
      border-top: 1px dashed var(--line);
      color: var(--muted);
      font-size: 13.5px;
    }
    dl.glo {
      display: grid;
      grid-template-columns: minmax(170px, auto) 1fr;
      gap: 9px 22px;
      margin: 12px 0 26px;
      align-items: baseline;
    }
    dl.glo dt { font-weight: 700; }
    dl.glo dd { margin: 0; color: var(--muted); font-size: 15px; }
    dl.glo dd a {
      margin-left: 4px;
      padding: 1px 6px;
      border: 1px solid var(--line);
      border-radius: 6px;
      color: var(--accent);
      font-size: 12px;
      font-weight: 700;
      text-decoration: none;
      white-space: nowrap;
    }
    dl.glo dd a:hover { border-color: var(--accent); background: var(--accent-2); }
    @media (max-width: 640px) {
      dl.glo { grid-template-columns: 1fr; gap: 2px; }
      dl.glo dt { margin-top: 12px; }
    }
"""

# sombras con tinte del shell original que quedaban fuera de los tokens
SOMBRAS_BASE = ["rgba(18, 44, 58, .1)", "rgba(15, 25, 22, .2)", "rgba(7, 23, 31, .36)"]


def _rel(p: Path) -> str:
    """Ruta legible para mensajes: relativa al directorio de trabajo si se
    puede (asi corren los wrappers, desde la raiz de cada repo de materia),
    absoluta si no."""
    try:
        return str(p.relative_to(Path.cwd()))
    except ValueError:
        return str(p)


def slug_kw(texto: str) -> str:
    t = unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode()
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    vistas, out = set(), []
    for w in t.split():
        if len(w) > 2 and w not in vistas:
            vistas.add(w)
            out.append(w)
    return " ".join(out)


def poner_figuras(frag: str, frag_dir: Path, uid: str) -> str:
    """Reemplaza <!--FIG:nombre--> por <frag_dir>/figuras/nombre.html.

    Las figuras son generadas (gen_figuras_<materia>.py, resultado commiteado)
    y no pasan por lint_fragmentos, asi que los vetos del contrato que les
    aplican se chequean aca, en cada build: nada de colores hardcodeados en
    SVG (romperian la paleta por materia y el modo oscuro), SVG accesible, y
    sin guiones largos ni middle dots.
    """
    def repl(m):
        nombre = m.group(1)
        f = frag_dir / "figuras" / f"{nombre}.html"
        if not f.exists():
            raise SystemExit(f"!! {uid}: falta la figura {_rel(f)}")
        cuerpo = f.read_text(encoding="utf-8").strip()
        fallas = []
        for c in re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{3,8}|rgb[^"]*)"', cuerpo):
            fallas.append(f"color hardcodeado {c}")
        for sm in re.finditer(r"<svg([^>]*)>", cuerpo):
            at = sm.group(1)
            if "viewBox" not in at:
                fallas.append("svg sin viewBox")
            if not any(a in at for a in ("aria-label", "aria-labelledby", "aria-hidden")):
                fallas.append("svg sin aria-label (o aria-hidden si es decorativo)")
        for mal, nom in ((chr(0x2014), "guion largo"), (chr(0x2013), "guion medio"),
                         (chr(0xB7), "middle dot")):
            if mal in cuerpo:
                fallas.append(nom)
        if fallas:
            raise SystemExit(f"!! figura {nombre} ({uid}): " + "; ".join(fallas))
        return cuerpo
    frag = re.sub(r"<!--\s*FIG:([a-z0-9-]+)\s*-->", repl, frag)
    if "<!--FIG" in frag:
        raise SystemExit(f"!! {uid}: marcador FIG con nombre invalido "
                         "(el formato es <!--FIG:nombre-en-kebab-->)")
    return frag


def copiar_imagenes(doc: str, frag_dir: Path, out_dir: Path) -> list:
    """Copia <frag_dir>/attachments/ -> <out_dir>/img/ y valida.

    Solo se copian las imagenes que el apunte referencia; una referencia sin
    archivo es error (pagina rota), un archivo sin referencia es aviso (peso
    muerto en el repo). Devuelve la lista de fallas.
    """
    att = frag_dir / "attachments"
    usadas = set(re.findall(r'src="img/([^"]+)"', doc))
    disponibles = {p.name for p in att.glob("*")} if att.exists() else set()
    faltan = sorted(usadas - disponibles)
    if faltan:
        return [f"imagenes referenciadas sin archivo en {att.name}/: {faltan[:6]}"]
    sobran = sorted(disponibles - usadas)
    if sobran:
        print(f"  aviso: attachments sin usar: {sobran[:6]}")
    if usadas:
        destino = out_dir / "img"
        destino.mkdir(parents=True, exist_ok=True)
        for n in sorted(usadas):
            shutil.copyfile(att / n, destino / n)
        print(f"  imagenes: {len(usadas)} copiadas a {_rel(destino)}/")
    return []


def transformar(frag: str, uid: str, numero: str) -> str:
    m = re.search(r"<h2[^>]*>(.*?)</h2>", frag, re.S)
    if not m:
        raise SystemExit(f"!! el fragmento {uid} no tiene <h2>")
    titulo = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
    titulo = re.sub(r"^[A-Z]?\d+\.\s*", "", titulo)

    heads = [re.sub(r"<[^>]+>", "", h) for h in
             re.findall(r"<h[34][^>]*>(.*?)</h[34]>", frag, re.S)]
    kw = slug_kw(titulo + " " + " ".join(heads))

    cuerpo = frag[m.end():].rstrip()
    if cuerpo.endswith("</section>"):
        cuerpo = cuerpo[: -len("</section>")]

    for viejo, nuevo in CLASES.items():
        cuerpo = cuerpo.replace(f'<div class="{viejo}">', f'<div class="{nuevo}">')

    def fix_details(mm):
        interior = mm.group(2)
        s = re.search(r"<summary>(.*?)</summary>", interior, re.S)
        if not s:
            return mm.group(0)
        return (f"<details><summary>{s.group(1)}</summary>"
                f'<div class="details-body">{interior[s.end():]}</div></details>')

    cuerpo = re.sub(r'<details class="(mas|preg)">(.*?)</details>',
                    fix_details, cuerpo, flags=re.S)

    # tablas: el shell las quiere envueltas para poder scrollearlas
    cuerpo = re.sub(r'<div class="tablewrap">\s*(<table>.*?</table>)\s*</div>',
                    r'<div class="table-wrap">\1</div>', cuerpo, flags=re.S)
    cuerpo = re.sub(r'(?<!<div class="table-wrap">)(<table>.*?</table>)',
                    lambda mm: f'<div class="table-wrap">{mm.group(1)}</div>',
                    cuerpo, flags=re.S)
    cuerpo = cuerpo.replace("<ul>\n    <li><b>", '<ul class="study-list">\n    <li><b>')
    # idem para listas donde el orden importa (un flujo, un proceso paso a
    # paso): mismo estilo de tarjeta, con numero en vez de vineta.
    cuerpo = cuerpo.replace("<ol>\n    <li><b>", '<ol class="study-list">\n    <li><b>')

    return (f'    <section class="chapter" id="{uid}" data-title="{kw}">\n'
            f'      <div class="chapter-head">\n'
            f'        <div class="chapter-number">{numero}</div>\n'
            f'        <div><h2>{titulo}</h2></div>\n'
            f'      </div>' + cuerpo + "\n    </section>\n")


def sidebar(grupos) -> str:
    partes = []
    for titulo, items in grupos:
        partes.append(f'    <div class="nav-title">{titulo}</div>')
        partes.append(f'    <nav class="toc" aria-label="{titulo}">')
        for uid, num, nombre in items:
            partes.append(f'      <a href="#{uid}"><span>{num}</span>{nombre}</a>')
        partes.append("    </nav>")
    return "\n".join(partes)


# Glifo de nodos compartido por el favicon y el icono de la PWA: la inicial de
# la materia no sirve como marca, y tenerlo una sola vez evita que diverjan.
# Ocupa el rango 10..54 de un viewBox de 64: entra en el 80% central, la zona
# segura de un icono maskable.
GLIFO_NODOS = ("<g stroke='white' stroke-width='3' fill='white'>"
               "<line x1='32' y1='32' x2='32' y2='14' />"
               "<line x1='32' y1='32' x2='16' y2='44' />"
               "<line x1='32' y1='32' x2='48' y2='44' />"
               "<circle cx='32' cy='32' r='6'/>"
               "<circle cx='32' cy='13' r='5'/>"
               "<circle cx='15' cy='45' r='5'/>"
               "<circle cx='49' cy='45' r='5'/>"
               "</g>")


def favicon_de(hexcolor: str) -> str:
    """Icono propio por materia, como data URI para la pestana."""
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
           f"<rect width='64' height='64' rx='14' fill='#{hexcolor}'/>"
           f"{GLIFO_NODOS}</svg>")
    return "data:image/svg+xml," + (svg.replace("#", "%23")
                                    .replace("<", "%3C").replace(">", "%3E"))


def icono_svg(hexcolor: str) -> str:
    """El mismo glifo como archivo suelto para el manifest de la PWA.

    Fondo a sangre completa y glifo en la zona segura: el mismo dibujo sirve
    para purpose "any" y "maskable" (la plataforma recorta la forma que quiera
    sin comerse el glifo).
    """
    return ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
            f"<rect width='64' height='64' fill='#{hexcolor}'/>"
            f"{GLIFO_NODOS}</svg>\n")


def manifest_de(cfg: dict) -> str:
    """Manifest de la PWA, derivado de la config de la materia.

    No hay campos nuevos que llenar: identidad, colores y descripcion son los
    mismos que ya usa la pagina. El fondo sale de --bg de la paleta clara.
    """
    fondo = re.search(r"--bg:\s*(#[0-9a-fA-F]+)", cfg["paleta_light"]).group(1)
    return json.dumps({
        "name": cfg["titulo_tab"],
        "short_name": cfg.get("nombre_corto", cfg["marca"]),
        "description": cfg["descripcion"],
        "lang": "es",
        "id": "./",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": fondo,
        "theme_color": cfg["theme_color"],
        "icons": [
            {"src": "icon.svg", "sizes": "any", "type": "image/svg+xml",
             "purpose": "any maskable"},
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png",
             "purpose": "any maskable"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png",
             "purpose": "any maskable"},
        ],
    }, ensure_ascii=False, indent=2) + "\n"


# Los PNG los rasteriza gen_iconos.py con ImageMagick y van commiteados: el
# build no depende de herramientas externas, aca solo se valida que existan.
ICONOS_PNG = ("icon-192.png", "icon-512.png", "apple-touch-icon.png")

SW_PLANTILLA = """\
// Generado por armar.py: no editar a mano.
// Precachea el apunte completo. La version del cache sale del hash del
// contenido: el archivo solo cambia cuando cambia algo, y ahi el navegador
// reinstala el service worker y renueva el cache en la visita siguiente.
const CACHE = '%(cache)s';
const ARCHIVOS = %(archivos)s;

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE)
    .then((c) => c.addAll(ARCHIVOS))
    .then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  // El CacheStorage es por origen, no por scope: se borran solo los caches
  // viejos de ESTA materia, sin pisar los de los otros apuntes.
  e.waitUntil(caches.keys()
    .then((claves) => Promise.all(claves
      .filter((k) => k.startsWith('%(prefijo)s') && k !== CACHE)
      .map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(caches.match(e.request, { ignoreSearch: true })
    .then((r) => r || fetch(e.request)));
});
"""


def generar_pwa(cfg: dict, out_dir: Path) -> list:
    """Escribe manifest.webmanifest, icon.svg y sw.js junto al apunte.

    El precache lista el apunte entero (pagina, manifest, iconos, imagenes):
    instalado, funciona completo sin red. Corre despues de copiar_imagenes
    para hashear lo que de verdad quedo en la salida.
    """
    fallas = []
    (out_dir / "icon.svg").write_text(icono_svg(cfg["favicon_hex"]),
                                      encoding="utf-8")
    (out_dir / "manifest.webmanifest").write_text(manifest_de(cfg),
                                                  encoding="utf-8")
    for png in ICONOS_PNG:
        if not (out_dir / png).exists():
            fallas.append(f"falta {png}: correr python3 gen_iconos.py")
    archivos = ["./", "./index.html", "./manifest.webmanifest", "./icon.svg"]
    archivos += [f"./{p}" for p in ICONOS_PNG]
    archivos += sorted(f"./{ruta}" for ruta in
                       set(re.findall(r'src="(img/[^"]+)"',
                                      (out_dir / "index.html")
                                      .read_text(encoding="utf-8"))))
    resumen = hashlib.sha256()
    for ruta in archivos:
        archivo = out_dir / ruta
        if archivo.is_file():
            resumen.update(archivo.read_bytes())
    (out_dir / "sw.js").write_text(SW_PLANTILLA % {
        "cache": f"{cfg['clave']}-{resumen.hexdigest()[:12]}",
        "prefijo": f"{cfg['clave']}-",
        "archivos": json.dumps(archivos, indent=2),
    }, encoding="utf-8")
    return fallas


def construir(cfg: dict, *, frag_dir: Path, out_dir: Path) -> int:
    """Arma el apunte de una materia.

    frag_dir: carpeta con los fragmentos (<prefijo><NN>.html) y, si aplica,
    figuras/ y attachments/. out_dir: carpeta de salida (ahi va index.html y
    todo lo de la PWA). Ambas las decide el repo de materia, no el motor:
    cfg["salida"] queda como metadata humana, ya no se usa para resolver
    rutas.
    """
    doc = SHELL.read_text(encoding="utf-8")

    # 1. capitulos
    ini = doc.find('<section class="chapter"')
    fin = doc.rfind("</section>") + len("</section>")
    capitulos, faltan = [], []
    for _, items in cfg["grupos"]:
        for uid, num, _ in items:
            f = frag_dir / f"{uid}.html"
            if not f.exists():
                faltan.append(f.name)
                continue
            frag = poner_figuras(f.read_text(encoding="utf-8"), frag_dir, uid)
            capitulos.append(transformar(frag, uid, num))
    if faltan:
        print(f"!! faltan fragmentos de {cfg['clave']}: {faltan}", file=sys.stderr)
        return 1
    doc = doc[:ini] + "\n".join(capitulos).lstrip() + doc[fin:]

    # 2. sidebar
    s_ini = doc.find('<div class="nav-title">')
    s_fin = doc.rfind("</nav>", 0, doc.find('class="side-actions"')) + len("</nav>")
    doc = doc[:s_ini] + sidebar(cfg["grupos"]).lstrip() + doc[s_fin:]

    # 3. identidad
    doc = re.sub(r"<title>.*?</title>", f"<title>{cfg['titulo_tab']}</title>",
                 doc, flags=re.S)
    doc = doc.replace("<strong>Aprendizaje Automático</strong>",
                      f"<strong>{cfg['marca']}</strong>")
    doc = re.sub(r'<header class="hero">.*?</header>',
                 f'<header class="hero">\n        <h1>{cfg["h1"]}</h1>\n'
                 f'        <p>{cfg["hero"]}</p>\n      </header>', doc, flags=re.S)
    doc = re.sub(r'<meta name="description" content="[^"]*"',
                 f'<meta name="description" content="{cfg["descripcion"]}"', doc)
    doc = doc.replace('content="Aprendizaje Automático"', f'content="{cfg["marca"]}"')

    # 4. estado propio en localStorage: los apuntes comparten dominio
    doc = re.sub(r"'aa-([a-z0-9-]+)'", rf"'{cfg['prefijo_ls']}-\1'", doc)

    # 5. paleta
    doc, n_l = re.subn(r":root\s*\{[^}]*\}", lambda _: cfg["paleta_light"], doc, count=1)
    doc, n_d = re.subn(r'html\[data-theme="dark"\]\s*\{[^}]*\}',
                       lambda _: cfg["paleta_dark"], doc, count=1)
    if not (n_l and n_d):
        print(f"!! no se pudo reemplazar la paleta (light={n_l}, dark={n_d})",
              file=sys.stderr)
        return 1
    for s in SOMBRAS_BASE:
        doc = doc.replace(s, "rgba(20, 20, 20, .18)")
    doc = doc.replace('content="#167e9e"', f'content="{cfg["theme_color"]}"')
    doc = doc.replace("</style>", CSS_EXTRA + "  </style>", 1)

    # 5 bis. autores
    try:
        doc = autoria.inyectar(doc, cfg.get("autores"))
    except ValueError as e:
        print(f"!! autoria de {cfg['clave']}: {e}", file=sys.stderr)
        return 1

    # 6. boton de la otra materia. La PWA del shell (link al manifest,
    # apple-touch-icon, boton de instalar y registro de sw.js) se conserva:
    # los hrefs son relativos y generar_pwa escribe esos archivos por materia.
    # Si esta materia tiene una segunda pagina (un resumen, un apunte
    # completo desde el resumen), boton_extra_href/texto lo re-apuntan en
    # vez de borrarlo; sin eso, se borra (no aplica a la mayoria).
    href_extra = cfg.get("boton_extra_href")
    texto_extra = cfg.get("boton_extra_texto")
    if href_extra and texto_extra:
        doc = re.sub(r'<a class="icon-button wide" href="resumen\.html">.*?</a>',
                     f'<a class="icon-button wide" href="{href_extra}">{texto_extra}</a>',
                     doc, flags=re.S)
    else:
        doc = re.sub(r'\s*<a class="icon-button wide" href="resumen\.html">.*?</a>', "",
                     doc, flags=re.S)
    doc = re.sub(r'<link rel="icon" href="data:image/png;base64,[^"]+"',
                 f'<link rel="icon" href="{favicon_de(cfg["favicon_hex"])}"', doc)

    # 7. sincronizacion entre dispositivos
    # Va al final del body: el modulo se cuelga solo del .side-actions y no
    # necesita que el shell le reserve nada. Un unico archivo para todos los
    # apuntes, para no tener copias divergiendo.
    # El reemplazo va como lambda y no como string: re.sub interpreta las
    # secuencias de escape del reemplazo, y convertiria los \n del JavaScript
    # en saltos de linea reales, partiendo los literales de texto al medio.
    for modulo in MODULOS:
        cuerpo = modulo.read_text(encoding="utf-8")
        marca = re.search(r'id="([a-z]+-dialog)"', cuerpo).group(1)
        if marca in doc:
            continue
        doc, n = re.subn(r"</body>", lambda _, c=cuerpo: c + "</body>", doc, count=1)
        if not n:
            print(f"!! no se encontro </body> para inyectar {modulo.name}", file=sys.stderr)
            return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    out.write_text(doc, encoding="utf-8")

    # 8. imagenes referenciadas
    fallas_img = copiar_imagenes(doc, frag_dir, out_dir)

    # 8 bis. PWA de la materia
    fallas_img += generar_pwa(cfg, out_dir)

    # 9. validacion
    ids = re.findall(r'\sid="([^"]+)"', doc)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    rotos = sorted({h for h in re.findall(r'href="#([^"]+)"', doc)} - set(ids))
    usados = set(re.findall(r"var\(\s*(--[a-z0-9-]+)", doc))
    huerfanos = sorted(usados - set(re.findall(r"(--[a-z0-9-]+)\s*:", doc)))
    externos = re.findall(r'(?:src|href)="https?://[^"]*"', doc)
    externos = [e for e in externos if "github.com" not in e]

    print(f"escrito: {_rel(out)}  "
          f"({len(doc.encode())//1024} KB, {len(capitulos)} capitulos)")
    print(f"  h3={len(re.findall(r'<h3', doc))} "
          f"callouts={len(re.findall(r'class=.callout', doc))} "
          f"svg={doc.count('<svg')} tablas={doc.count('<table')}")
    if dup:
        print(f"  !! ids duplicados: {dup[:8]}")
    if rotos:
        print(f"  !! anclas rotas: {rotos[:8]}")
    if huerfanos:
        print(f"  !! tokens CSS sin definir: {huerfanos}")
    if externos:
        print(f"  !! recursos externos: {externos[:4]}")
    for f_img in fallas_img:
        print(f"  !! {f_img}")
    if not (dup or rotos or huerfanos or externos or fallas_img):
        print("  ids unicos, anclas resuelven, tokens definidos, imagenes en su "
              "lugar, sin recursos externos, PWA al dia")
    return 1 if (dup or rotos or huerfanos or externos or fallas_img) else 0
