# Contrato para fragmentos de capítulo

Cada capítulo es UN archivo `<frag_dir>/<prefijo><NN>.html` que contiene
exactamente un `<section>` y nada más (sin doctype, html, head, body, sin
`<style>` ni `<script>` propios, sin recursos externos de ningún tipo).
`frag_dir` y `prefijo` los define cada repo de materia, no el motor.

## Estructura

```html
<section class="unidad" id="UIDNN" data-titulo="Titulo corto">
  <h2>UIDNN. Titulo del capitulo</h2>
  <p class="intro">2-4 oraciones: que cubre el capitulo y por que importa.</p>

  <h3 id="UIDNN-tema-slug">Tema</h3>
  ...contenido...
</section>
```

- Encabezados: h2 solo el título del capítulo, h3 temas, h4 subtemas. Todos
  los h3/h4 con id prefijado `<uid>-` (el índice y la búsqueda se generan
  de ahí).
- Idioma: español rioplatense neutro, técnico. Términos en inglés cuando son
  de uso universal (commit, quorum, broker), sin traducciones forzadas.
- ORTOGRAFÍA: el texto visible va con TILDES correctas (comunicación,
  función, también, está, qué). La regla de abajo prohíbe guiones largos, NO
  prohíbe acentos: un apunte en español sin tildes está mal escrito. Los
  identificadores (id, href) y el código van sin acentos.
- Sin guiones largos ni middle dots en el texto: comas, dos puntos o
  paréntesis.

## Vocabulario de clases (usar estas, no inventar)

- `<div class="def">` definición formal de un concepto. Primer elemento
  interno: `<b>Término.</b>` seguido de la definición.
- `<div class="idea">` intuición o forma de pensar un concepto (complementa
  def).
- `<div class="ej">` ejemplo concreto desarrollado.
- `<div class="warn">` error común o distinción sutil que confunde en
  exámenes.
- `<div class="examen">` señal de final: indica que esto fue preguntado en
  finales, citando la forma típica de la pregunta. Ej: "Preguntado en
  finales: 'Compare X con Y' (2025-07, 2024-12)".
- `<details class="mas"><summary>...</summary>...</details>` para
  profundizaciones opcionales (demostraciones, casos borde, material que
  excede la clase).
- `<table>` para comparaciones. Siempre con `<thead>`.
- `<figure class="diag">` para diagramas: SVG inline simple (cajas, flechas,
  texto) + `<figcaption>`. Paleta del SVG: solo `currentColor` y los tokens
  `var(--acc)` (acento), `var(--acc2)` (secundario, anotaciones y líneas
  punteadas), `var(--linea)` (trazo neutro, cajas y flechas), y para
  gráficos con datos: `var(--acc3)` (serie cálida), `var(--acc4)` (serie de
  riesgo o alerta) y `var(--grid)` (retícula, más tenue que --linea). Nada
  de colores hardcodeados.
  Esos nombres NO son tokens del shell: `armar.py` (`CSS_EXTRA`) los define
  como alias sobre tokens reales que se ven en los dos temas. Si se agrega
  un token nuevo al vocabulario hay que definir el alias ahí, o el SVG se
  rompe en silencio: un `var()` no definido en `stroke` computa a `none` y
  la flecha se vuelve invisible sin ningún error.
- `<code>` inline y `<pre><code>` para pseudocódigo.
- `<p class="nota">` acotación de contexto sobre un bloque.
- `<p class="ref">` cierre de una sección con enlaces a otras partes del
  apunte donde se profundiza el tema.
- `<dl class="glo">` glosario, si el repo de materia genera uno con su
  propio script (no es parte del motor).
- `<div class="formula">` recuadro para una fórmula suelta (la sintaxis usa
  `<sub>`/`<sup>`; multiplicación con la x de multiplicar, nunca middle dot).

## Figuras generadas e imágenes (opcionales por materia)

- `<!--FIG:nombre-->` inserta `<frag_dir>/figuras/nombre.html` al armar. Es
  para figuras que salen de un script (gráficos con datos, tablas
  calculadas, tarjetas): un script propio del repo de materia
  (`gen_figuras_<materia>.py`, no forma parte del motor) las escribe y su
  resultado va commiteado, así el build nunca depende de correrlo. Las
  figuras cumplen las mismas reglas de color y accesibilidad que los SVG de
  fragmento (armar.py las valida en cada build); un SVG puramente decorativo
  puede llevar `aria-hidden="true"` en vez de `aria-label`.
- `<img src="img/nombre.png">` (dentro de `figure.diag`, con figcaption)
  referencia una imagen de `<frag_dir>/attachments/`. Nombres descriptivos
  en kebab-case, nunca hashes. El build copia a `<salida>/img/` solo las
  imágenes usadas, falla si falta alguna y avisa si sobran. Antes de sumar
  una imagen, preguntarse si no conviene un SVG con tokens: la imagen no se
  adapta al tema ni a la paleta (el shell le pone fondo blanco para que
  sobreviva al modo oscuro).

## Contenido

- Autocontenido: el lector NO tiene las diapositivas ni la clase grabada.
  Nada de "como se vio en la filmina". Todo concepto usado se define antes o
  se linkea con `<a href="#uid-slug">`.
- Densidad: esto es un apunte de estudio, no un libro. Párrafos cortos,
  listas, tablas. Cada afirmación tiene que ganarse el lugar.
- No inventar contenido que no esté respaldado por alguna fuente. Ante duda,
  el bloque `.warn` puede decir "la cátedra no lo cubre en profundidad".

## Prohibido

- Recursos externos (fonts, imágenes, CDNs). Todo inline.
- Datos personales de alumnos que aparezcan en las fuentes (nombres,
  padrones).
- Inventar contenido que no esté respaldado por alguna fuente.

## Validar

```
python3 -m motor_apuntes.lint_fragmentos <frag_dir o archivo.html> ...
```
Tiene que dar "0 hallazgo(s)".
