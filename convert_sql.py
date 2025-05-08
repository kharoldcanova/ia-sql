import sqlparse
from ollama import chat
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# Prompt base simplificado para reducir overhead
BASE_PROMPT = (
    "Eres un asistente que documenta esquemas SQL en Markdown.\n"
    "Recibe sólo las declaraciones SQL de una misma tabla y devuelve:\n"
    "- Nombre de la tabla en mayúsculas\n"
    "- Descripción breve\n"
    "- Campos (nombre, tipo, explicación)\n"
    "- Relaciones (llaves foráneas)\n\n"
    "Ejemplo:\n"
    "SQL: CREATE TABLE Roles (id_rol INT PRIMARY KEY, nombre VARCHAR(50));\n"
    "MD:\n"
    "**ROLES**\n"
    "- **Descripción:** Guarda los roles de usuarios.\n"
    "- **Campos:**\n"
    "  - **id_rol (INT):** Clave primaria de la tabla Roles.\n"
    "  - **nombre (VARCHAR(50)):** Nombre del rol.\n"
    "- **Relaciones:** Ninguna.\n"
)


def segmentar_sql(ruta_sql: str) -> list[str]:
    """
    Lee el archivo SQL y crea fragmentos en cada `;`, descartando segmentos
    que sólo contengan comentarios. Usa sqlparse.split para respetar
    strings y paréntesis.
    """
    with open(ruta_sql, encoding='utf-8') as f:
        contenido = f.read()
    # sqlparse.split divide por ; respetando contexto
    raw_stmts = sqlparse.split(contenido)
    # Filtrar segmentos vacíos o sólo comentarios
    stmts = []
    for stmt in raw_stmts:
        text = stmt.strip()
        if not text:
            continue
        # descartamos fragmentos que sólo empiecen con comentario
        if re.match(r"^--", text):
            continue
        # asegurar punto y coma
        if not text.endswith(';'):
            text += ';'
        stmts.append(text)
    return stmts


def get_table_name(stmt: str) -> str | None:
    """
    Extrae el nombre de la tabla de una sentencia DDL. Soporta opcional
    prefijo de esquema (schema.table) y backticks.
    """
    # Permite `schema`.`table` o schema.table o sólo table
    pattern = (
        r"(?:CREATE|DROP|ALTER)\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+"
        r"(?:`?(?:\w+)`?\.)?`?(\w+)`?"
    )
    m = re.search(pattern, stmt, re.IGNORECASE)
    return m.group(1) if m else None


def agrupar_por_tabla(statements: list[str]) -> dict[str, list[str]]:
    """
    Agrupa sentencias por nombre de tabla. Las que no tienen tabla
    se agrupan bajo '_otros_'.
    """
    grupos: dict[str, list[str]] = {}
    for stmt in statements:
        tabla = get_table_name(stmt) or '_otros_'
        grupos.setdefault(tabla, []).append(stmt)
    return grupos


def transcribir_segmento(seg: str, modelo: str = 'deepseek-r1:8b') -> str:
    """
    Envía al modelo las declaraciones SQL (DROP + CREATE + ALTER) de una misma tabla.
    """
    prompt = f"{BASE_PROMPT}\nSQL:\n{seg}\n\nMD:"
    resp = chat(model=modelo, messages=[{"role": "user", "content": prompt}])
    return resp.message.content.strip()


def transcribir_sql(
    archivo_sql: str,
    archivo_md: str,
    modelo: str = 'deepseek-r1:8b',
    max_workers: int = 4
):
    """
    Lee y segmenta el SQL, agrupa sentencias por tabla, paraleliza las llamadas
    y escribe el resultado en Markdown.
    """
    statements = segmentar_sql(archivo_sql)
    grupos = agrupar_por_tabla(statements)
    tablas = sorted(grupos.keys(), key=lambda t: (t=='_otros_', t))

    resultados: dict[str, str] = {}
    with open(archivo_md, 'w', encoding='utf-8') as out, \
         ThreadPoolExecutor(max_workers=max_workers) as executor:

        futures = {
            executor.submit(
                transcribir_segmento,
                '\n'.join(grupos[tabla]),
                modelo
            ): tabla
            for tabla in tablas if tabla != '_otros_'
        }
        for futuro in as_completed(futures):
            tabla = futures[futuro]
            try:
                md = futuro.result()
            except Exception as e:
                md = f"Error al procesar tabla {tabla}: {e}"
            # Escribir cada resultado en cuanto esté listo
            out.write(md + '\n\n--- Fin de ' + tabla + ' ---\n\n')
            print(f"Terminado tabla {tabla}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Documenta tablas SQL en Markdown usando Ollama.'
    )
    parser.add_argument(
        'input_sql', nargs='?', default='./data/teams.sql',
        help='Ruta al archivo .sql de entrada (por defecto %(default)s)'
    )
    parser.add_argument(
        'output_md', nargs='?', default='./documents/markdown_database.md',
        help='Ruta al archivo .md de salida (por defecto %(default)s)'
    )
    parser.add_argument('--model', default='deepseek-r1:8b',
                        help='Nombre del modelo Ollama a usar')
    parser.add_argument('--workers', type=int, default=4,
                        help='Número de hilos para paralelizar')

    args = parser.parse_args()
    transcribir_sql(
        args.input_sql,
        args.output_md,
        modelo=args.model,
        max_workers=args.workers
    )
