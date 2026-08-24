# motor-apuntes

Motor compartido de la plataforma [fiuba-resumenes](https://fiuba-resumenes.github.io):
arma un apunte de FIUBA a partir de fragmentos HTML sobre un shell común
(búsqueda, resaltador, notas, tema oscuro, sincronización entre
dispositivos), y le genera una PWA instalable (manifest, service worker,
íconos).

Cada materia vive en su propio repo bajo el org `fiuba-resumenes`, con su
propio contenido y su propia config, y depende de una versión fija de este
paquete. Una mejora acá no rompe todas las materias de un día para el otro:
cada repo sube el pin cuando quiere.

## Instalar

```
pip install "motor-apuntes @ git+https://github.com/fiuba-resumenes/motor@v0.1.0"
```

(No hay paquete en PyPI: los tags de este repo son el mecanismo de release.)

## Usar

Cada repo de materia trae su propia config (un dict, no un módulo
compartido) y un wrapper chico que llama al motor:

```python
# fuentes/materia.py
CFG = {
    "clave": "redes",
    "codigo": "TA048",
    "catedra": "Alvarez Hamelin",
    "autores": ["echepereza", "flopeztancredi"],
    "prefijo_ls": "rd",
    "titulo_tab": "Redes (75.43) - Apunte completo",
    "marca": "Redes",
    "h1": "Redes",
    "hero": "...",
    "descripcion": "...",
    "theme_color": "#a06520",
    "favicon_hex": "a06520",
    "grupos": [...],
    "paleta_light": "...",
    "paleta_dark": "...",
}
```

```python
#!/usr/bin/env python3
# armar.py (en la raiz del repo de materia)
import sys
from pathlib import Path
from motor_apuntes.armar import construir
from fuentes.materia import CFG

if __name__ == "__main__":
    sys.exit(construir(CFG, frag_dir=Path("fuentes"), out_dir=Path(".")))
```

Fragmentos: `fuentes/<prefijo><NN>.html`, uno por capítulo, según
`contrato-fragmento.md` (ver `motor_apuntes/contrato-fragmento.md` en este
paquete). Validar antes de armar:

```
python3 -m motor_apuntes.lint_fragmentos fuentes/
```

Íconos PNG de la PWA (una vez, o cuando cambia `favicon_hex`; requiere
ImageMagick, no es parte del build):

```python
# gen_iconos.py (en la raiz del repo de materia)
import sys
from pathlib import Path
from motor_apuntes.gen_iconos import generar
from fuentes.materia import CFG

if __name__ == "__main__":
    sys.exit(generar(CFG, Path(".")) or 0)
```

## Qué NO es parte de este paquete

- `gen_figuras_<materia>.py`: generador de figuras con datos, específico de
  cada materia. El contrato solo documenta la convención `<!--FIG:nombre-->`
  que usa para insertarlas.
- Cualquier pipeline extra que una materia necesite (autoevaluación,
  glosario, un resumen aparte): son scripts propios de ese repo que producen
  fragmentos comunes o llaman a `construir()` una segunda vez.

## Versionado

SemVer por tag de git. Un cambio que rompe la firma de `construir()`, el
contrato de fragmentos, o el layout de `CFG` es mayor; todo lo demás, menor
o parche.
