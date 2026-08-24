"""Bloque de autores al pie de la barra lateral: logo de GitHub y usuario.

Sin `autores` el build falla, a proposito.
"""
import html
import re

# Octicon mark-github-16.
MARCA = (
    '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 '
    '3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53'
    '-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 '
    '1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95'
    ' 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27'
    ' 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56'
    '.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93'
    '-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>'
)

CSS = """
    .autoria {
      display: flex;
      flex-direction: column;
      gap: 7px;
      margin-top: 18px;
      padding-top: 14px;
      border-top: 1px solid var(--line);
    }
    .autoria a {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      color: var(--muted);
      font-size: 12.5px;
      text-decoration: none;
    }
    .autoria a:hover { color: var(--accent); }
    .autoria svg { flex: none; width: 14px; height: 14px; fill: currentColor; }
"""

# Formato de usuario de GitHub. Se valida porque entra crudo a una URL.
USUARIO = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")


def bloque(autores) -> str:
    if not autores:
        raise ValueError("la materia no declara autores")
    enlaces = []
    # Alfabetico y no en el orden declarado: ninguno es mas autor que el otro,
    # y asi el orden no es una decision que alguien pueda leer como jerarquia.
    for u in sorted(autores, key=str.lower):
        if not USUARIO.match(u):
            raise ValueError(f"usuario de GitHub invalido: {u!r}")
        seguro = html.escape(u)
        enlaces.append(
            f'      <a href="https://github.com/{seguro}" rel="author noopener"'
            f' title="Autor del apunte">{MARCA}{seguro}</a>'
        )
    return '    <div class="autoria">\n' + "\n".join(enlaces) + "\n    </div>\n"


def inyectar(doc: str, autores) -> str:
    """Idempotente: reemplaza la firma que haya en vez de acumular otra."""
    doc = re.sub(r'[ \t]*<div class="autoria">.*?</div>\n?', "", doc, flags=re.S)
    # Por bloque y no por cadena exacta: si cambia el CSS, la version vieja
    # tiene que salir igual, sin dejar restos.
    doc = re.sub(r"\n(?:[ \t]*/\*(?:(?!\*/).)*?\*/[ \t]*\n)?"
                 r"[ \t]*\.autoria \{.*?\.autoria svg \{[^}]*\}\n",
                 "", doc, flags=re.S)

    # El ancla se come la sangria de </style>: si no, cada pasada corre el CSS
    # dos espacios mas a la derecha.
    doc, n = re.subn(r"[ \t]*</style>", lambda _: CSS + "  </style>", doc, count=1)
    if not n:
        raise ValueError("no se encontro </style> para el CSS de autoria")

    # El primer </aside> es la barra lateral; el segundo, el panel de notas.
    doc, n = re.subn(r"[ \t]*</aside>",
                     lambda _, b=bloque(autores): b + "  </aside>", doc, count=1)
    if not n:
        raise ValueError("no se encontro </aside> para la firma de autoria")
    return doc
