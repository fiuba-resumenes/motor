#!/usr/bin/env python3
"""Agrega tildes y enies al texto visible de los fragmentos del apunte.

Opera SOLO sobre el texto fuera de etiquetas: saltea <pre> y <code>
(pseudocodigo e identificadores van sin acentos) y no toca atributos.
El texto de las etiquetas de los <svg> SI se acentua: es prosa, y saltear
los svg fue lo que dejo todos los diagramas escritos sin tildes.

Uso: python3 -m motor_apuntes.herramientas.acentuar archivo.html [...]
     (edita en el lugar)
"""
import re
import sys
from pathlib import Path

# --- 1. palabras sin ambiguedad: una sola forma correcta ---------------------
PALABRAS = {
    # -stion no lo cubre la regla de sufijos (-cion, -sion, -xion)
    "congestion": "congestión", "gestion": "gestión",
    "cuestion": "cuestión", "digestion": "digestión",
    "sugestion": "sugestión", "combustion": "combustión",
    # vocabulario tecnico de la materia que faltaba en la primera pasada
    "patron": "patrón", "patrones": "patrones",
    "anonima": "anónima", "anonimo": "anónimo",
    "anonimas": "anónimas", "anonimos": "anónimos",
    "heterogeneo": "heterogéneo", "heterogenea": "heterogénea",
    "heterogeneos": "heterogéneos", "heterogeneas": "heterogéneas",
    "homogeneo": "homogéneo", "homogenea": "homogénea",
    "homogeneos": "homogéneos", "homogeneas": "homogéneas",
    "jerarquia": "jerarquía", "jerarquias": "jerarquías",
    "jerarquico": "jerárquico", "jerarquica": "jerárquica",
    "jerarquicos": "jerárquicos", "jerarquicas": "jerárquicas",
    "analogo": "análogo", "analoga": "análoga",
    "analogos": "análogos", "analogas": "análogas",
    "pesimamente": "pésimamente", "disenio": "diseño",
    # comparativo y adverbios
    "mas": "más", "ademas": "además", "tambien": "también", "asi": "así",
    "despues": "después", "segun": "según", "ahi": "ahí", "aqui": "aquí",
    "alli": "allí", "quiza": "quizá", "solamente": "solamente",
    # verbos con forma unica
    "estan": "están", "sera": "será", "seran": "serán", "seria": "sería",
    "serian": "serían", "podria": "podría", "podrian": "podrían",
    "habra": "habrá", "habria": "habría", "tendra": "tendrá",
    "tendran": "tendrán", "tendria": "tendría", "hara": "hará",
    "haran": "harán", "dara": "dará", "daran": "darán", "vendra": "vendrá",
    "sabra": "sabrá", "envia": "envía", "envian": "envían", "envie": "envíe",
    "confia": "confía", "confian": "confían", "varia": "varía",
    "varian": "varían", "verifica": "verifica", "actua": "actúa",
    "actuan": "actúan", "continua": "continúa", "continuan": "continúan",
    "leido": "leído", "leida": "leída", "caido": "caído", "caida": "caída",
    "caidos": "caídos", "caidas": "caídas", "traido": "traído",
    "oido": "oído", "creido": "creído", "reune": "reúne", "reunen": "reúnen",
    # sustantivos y adjetivos
    "lider": "líder", "lideres": "líderes", "replica": "réplica",
    "replicas": "réplicas", "mayoria": "mayoría", "mayorias": "mayorías",
    "minoria": "minoría", "unico": "único", "unica": "única",
    "unicos": "únicos", "unicas": "únicas", "numero": "número",
    "numeros": "números", "metodo": "método", "metodos": "métodos",
    "parametro": "parámetro", "parametros": "parámetros",
    "maquina": "máquina", "maquinas": "máquinas", "tecnica": "técnica",
    "tecnicas": "técnicas", "tecnico": "técnico", "tecnicos": "técnicos",
    "catedra": "cátedra", "codigo": "código", "codigos": "códigos",
    "practica": "práctica", "practicas": "prácticas", "practico": "práctico",
    "practicos": "prácticos", "critica": "crítica", "criticas": "críticas",
    "critico": "crítico", "criticos": "críticos", "analisis": "análisis",
    "sintesis": "síntesis", "hipotesis": "hipótesis", "enfasis": "énfasis",
    "indice": "índice", "indices": "índices", "arbol": "árbol",
    "arboles": "árboles", "linea": "línea", "lineas": "líneas",
    "area": "área", "areas": "áreas", "util": "útil", "utiles": "útiles",
    "facil": "fácil", "faciles": "fáciles", "dificil": "difícil",
    "dificiles": "difíciles", "rapido": "rápido", "rapida": "rápida",
    "rapidos": "rápidos", "rapidas": "rápidas", "maximo": "máximo",
    "maxima": "máxima", "maximos": "máximos", "maximas": "máximas",
    "minimo": "mínimo", "minima": "mínima", "minimos": "mínimos",
    "minimas": "mínimas", "optimo": "óptimo", "optima": "óptima",
    "ultimo": "último", "ultima": "última", "ultimos": "últimos",
    "ultimas": "últimas", "proximo": "próximo", "proxima": "próxima",
    "multiple": "múltiple", "multiples": "múltiples", "dia": "día",
    "dias": "días", "via": "vía", "vias": "vías", "energia": "energía",
    "garantia": "garantía", "garantias": "garantías",
    "jerarquia": "jerarquía", "jerarquias": "jerarquías",
    "anomalia": "anomalía", "anomalias": "anomalías",
    "categoria": "categoría", "categorias": "categorías",
    "tecnologia": "tecnología", "tecnologias": "tecnologías",
    "topologia": "topología", "topologias": "topologías",
    "metodologia": "metodología", "politica": "política",
    "politicas": "políticas", "metrica": "métrica", "metricas": "métricas",
    "semantica": "semántica", "semanticas": "semánticas",
    "semantico": "semántico", "aritmetica": "aritmética",
    "informatica": "informática", "matematica": "matemática",
    "estadistica": "estadística", "heuristica": "heurística",
    "caracteristica": "característica", "caracteristicas": "características",
    "problematica": "problemática", "tematica": "temática",
    "razon": "razón", "razones": "razones", "perdida": "pérdida",
    "perdidas": "pérdidas", "margen": "margen", "orden": "orden",
    # -ico / -ica tecnicos
    "atomico": "atómico", "atomica": "atómica", "atomicos": "atómicos",
    "atomicas": "atómicas", "automatico": "automático",
    "automatica": "automática", "automaticos": "automáticos",
    "automaticas": "automáticas", "teorico": "teórico", "teorica": "teórica",
    "logico": "lógico", "logica": "lógica", "logicos": "lógicos",
    "logicas": "lógicas", "fisico": "físico", "fisica": "física",
    "fisicos": "físicos", "fisicas": "físicas", "estatico": "estático",
    "estatica": "estática", "estaticos": "estáticos",
    "dinamico": "dinámico", "dinamica": "dinámica",
    "dinamicos": "dinámicos", "dinamicas": "dinámicas",
    "periodico": "periódico", "periodica": "periódica",
    "periodicos": "periódicos", "periodicamente": "periódicamente",
    "monotonico": "monotónico", "monotonica": "monotónica",
    "economico": "económico", "economica": "económica",
    "especifico": "específico", "especifica": "específica",
    "especificos": "específicos", "especificas": "específicas",
    "basico": "básico", "basica": "básica", "basicos": "básicos",
    "basicas": "básicas", "clasico": "clásico", "clasica": "clásica",
    "clasicos": "clásicos", "clasicas": "clásicas", "tipico": "típico",
    "tipica": "típica", "tipicos": "típicos", "tipicas": "típicas",
    "sincronico": "sincrónico", "sincronica": "sincrónica",
    "sincronicos": "sincrónicos", "sincronicas": "sincrónicas",
    "asincronico": "asincrónico", "asincronica": "asincrónica",
    "asincronicos": "asincrónicos", "asincronicas": "asincrónicas",
    "deterministico": "determinístico", "deterministica": "determinística",
    "deterministicas": "determinísticas", "simetrico": "simétrico",
    "asimetrico": "asimétrico", "asimetrica": "asimétrica",
    "electronico": "electrónico", "electronica": "electrónica",
    "geografico": "geográfico", "geografica": "geográfica",
    "grafico": "gráfico", "grafica": "gráfica", "graficos": "gráficos",
    "graficas": "gráficas", "practicamente": "prácticamente",
    "automaticamente": "automáticamente", "unicamente": "únicamente",
    "logicamente": "lógicamente", "tipicamente": "típicamente",
    "basicamente": "básicamente", "rapidamente": "rápidamente",
    "facilmente": "fácilmente", "dificilmente": "difícilmente",
    # enies
    "diseno": "diseño", "disenos": "diseños", "disenar": "diseñar",
    "disenado": "diseñado", "disenada": "diseñada", "disenados": "diseñados",
    "disenadas": "diseñadas", "disene": "diseñe", "senal": "señal",
    "senales": "señales", "senalar": "señalar", "senala": "señala",
    "pequeno": "pequeño", "pequena": "pequeña", "pequenos": "pequeños",
    "pequenas": "pequeñas", "tamano": "tamaño", "tamanos": "tamaños",
    "manana": "mañana", "compania": "compañía", "desempeno": "desempeño",
    "extrano": "extraño", "ensena": "enseña", "duenio": "dueño",
    "anio": "año", "anios": "años",
    # segunda pasada: detectadas revisando el corpus
    "pagina": "página", "paginas": "páginas", "computo": "cómputo",
    "formula": "fórmula", "formulas": "fórmulas", "multiplo": "múltiplo",
    "termino": "término", "terminos": "términos", "proposito": "propósito",
    "transito": "tránsito", "limite": "límite", "limites": "límites",
    "trafico": "tráfico", "grafo": "grafo", "grafos": "grafos",
    "topico": "tópico", "topicos": "tópicos", "modulo": "módulo",
    "modulos": "módulos", "circulo": "círculo", "generico": "genérico",
    "generica": "genérica", "genericos": "genéricos",
    "algoritmica": "algorítmica", "algoritmico": "algorítmico",
    "capitulo": "capítulo", "titulo": "título", "articulo": "artículo",
    "parrafo": "párrafo", "telefono": "teléfono", "vinculo": "vínculo",
    "numerico": "numérico", "numerica": "numérica",
    "simbolico": "simbólico", "historico": "histórico",
    "geometrico": "geométrico", "cronologico": "cronológico",
}

# --- 2. reglas de sufijo (validas para la palabra completa) -----------------
SUFIJOS = [
    (re.compile(r"\b([a-zA-Z]{2,}?)cion\b"), r"\1ción"),
    (re.compile(r"\b([a-zA-Z]{2,}?)sion\b"), r"\1sión"),
    (re.compile(r"\b([a-zA-Z]{2,}?)xion\b"), r"\1xión"),
]

# --- 3. "esta" solo cuando es el verbo -------------------------------------
# El demostrativo va seguido de sustantivo; el verbo, de participio,
# adjetivo de estado, adverbio o preposicion.
ESTA_VERBO = re.compile(
    r"\besta\s+(?="
    r"(?:[a-zñáéíóú]+(?:ado|ada|ados|adas|ido|ida|idos|idas|ando|endo)\b)"
    r"|(?:en|dentro|fuera|muy|bien|mal|siempre|nunca|listo|lista|libre|"
    r"lleno|llena|vacia|vacio|activo|activa|disponible|vivo|viva|"
    r"garantizado|garantizada|acotado|acotada|abierto|abierta|cerrado|"
    r"cerrada|ocupado|ocupada|necesariamente|obligado|sujeto|por|entre|"
    r"al|ahi|ahí|arriba|abajo|cerca|lejos|solo|sola|aun|aún|ya|todavia|"
    r"todavía|de\s+acuerdo|del\s+lado)\b"
    # adjetivos de estado en -ante/-ente/-ible/-able (intermitente, estable)
    r"|(?:[a-zñáéíóú]+(?:ante|ente|ible|able)\b)"
    r")"
)

# --- 4. interrogativos: solo tras signo de apertura ------------------------
INTERROG = {
    "que": "qué", "cual": "cuál", "cuales": "cuáles", "como": "cómo",
    "donde": "dónde", "cuando": "cuándo", "quien": "quién",
    "quienes": "quiénes", "cuanto": "cuánto", "cuantos": "cuántos",
    "cuanta": "cuánta", "cuantas": "cuántas", "por que": "por qué",
}

# Se protege el codigo y TODOS los tags (o sea, los valores de atributos).
# Los bloques <svg> NO se protegen enteros a proposito: el texto de las
# etiquetas de un diagrama es prosa y tambien lleva tildes. Saltearlos fue
# el punto ciego que dejo los diagramas escritos sin acentos.
PROTEGIDO = re.compile(r"(<pre\b.*?</pre>|<code\b.*?</code>|<[^>]+>)",
                       re.S | re.I)


def acentuar_texto(s: str) -> str:
    for pat, rep in SUFIJOS:
        s = pat.sub(rep, s)

    def una(m):
        w = m.group(0)
        low = w.lower()
        if low not in PALABRAS:
            return w
        nuevo = PALABRAS[low]
        if w[0].isupper():
            nuevo = nuevo[0].upper() + nuevo[1:]
        return nuevo

    s = re.sub(r"\b[a-zA-ZñÑ]+\b", una, s)
    s = ESTA_VERBO.sub("está ", s)

    def interr(m):
        signo, palabra = m.group(1), m.group(2)
        rep = INTERROG.get(palabra.lower())
        if not rep:
            return m.group(0)
        if palabra[0].isupper():
            rep = rep[0].upper() + rep[1:]
        return signo + rep

    s = re.sub(r"(¿\s*)([A-Za-zñÑ]+)", interr, s)
    return s


def main() -> int:
    total = 0
    for arg in sys.argv[1:]:
        p = Path(arg)
        txt = p.read_text(encoding="utf-8")
        partes = PROTEGIDO.split(txt)
        # los indices impares son las regiones protegidas
        for i in range(0, len(partes), 2):
            partes[i] = acentuar_texto(partes[i])
        nuevo = "".join(partes)
        antes = sum(txt.count(c) for c in "áéíóúÁÉÍÓÚñÑ")
        despues = sum(nuevo.count(c) for c in "áéíóúÁÉÍÓÚñÑ")
        p.write_text(nuevo, encoding="utf-8")
        print(f"  {p.name:16} +{despues - antes} diacriticos")
        total += despues - antes
    print(f"  total: +{total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
