import re
from ollama import chat

def segmentar_sql(archivo_sql):
    contenido = open(archivo_sql, encoding='utf-8').read()
    # Segmenta en declaraciones completas considerando comentarios y bloques
    patrones = re.split(r';\s*(?=CREATE|ALTER|INSERT|UPDATE|DELETE|DROP)', contenido, flags=re.IGNORECASE)
    return [seg.strip() + ';' for seg in patrones if seg.strip()]

SYSTEM_MSG = (
    "Eres un asistente que documenta esquemas SQL en Markdown. "
    "Recibe una sola declaración SQL y devuelve una descripción con:\n"
    "- Nombre de la tabla en mayúsculas\n"
    "- Descripción breve\n"
    "- Campos (nombre, tipo, explicación)\n"
    "- Relaciones (llaves foráneas)\n"
)

EXAMPLE = (
    "SQL:\nCREATE TABLE Roles (id_rol INT PRIMARY KEY, nombre VARCHAR(50));\n"
    "MD:\n**ROLES**\n- **Descripción:** Guarda los roles de usuarios.\n"
    "- **Campos:**\n"
    "  - **id_rol (INT):** Clave primaria de la tabla Roles.\n"
    "  - **nombre (VARCHAR(50)):** Nombre del rol.\n"
    "- **Relaciones:** Ninguna.\n"
)

def transcribir_segmento(seg, modelo='deepseek-r1:8b'):
    prompt = f"{SYSTEM_MSG}\nEjemplo:\n{EXAMPLE}\nSQL:\n{seg}\nMD:"
    resp = chat(model=modelo, messages=[
        {"role": "system", "content": SYSTEM_MSG},
        {"role": "user",   "content": EXAMPLE},
        {"role": "user",   "content": prompt}
    ])
    return resp.message.content.strip()

def transcribir_sql(archivo_sql, archivo_md):
    segmentos = segmentar_sql(archivo_sql)
    with open(archivo_md, 'w', encoding='utf-8') as out:
        for i, seg in enumerate(segmentos, 1):
            print(f"Procesando {i}/{len(segmentos)}")
            md = transcribir_segmento(seg)
            out.write(md + '\n\n--- Fin de Segmento ---\n\n')

# Uso de la función
if __name__ == "__main__":
    transcribir_sql('./data/teams.sql', './documents/markdown_database.md')
