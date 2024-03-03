from openai import OpenAI
import dotenv
import os

def segmentar_sql(archivo_sql):
    """
    Segmenta el archivo SQL en declaraciones completas.

    :param archivo_sql: Ruta del archivo SQL de entrada.
    :return: Lista de segmentos SQL.
    """
    with open(archivo_sql, 'r', encoding='utf-8') as archivo:
        contenido = archivo.read()
        # Aquí puedes implementar una lógica más sofisticada para segmentar correctamente
        segmentos = contenido.split(';')
        return [seg.strip() + ';' for seg in segmentos if seg.strip()]

def transcribir_segmento(segmento, client):
    """
    Transcribe un segmento SQL a lenguaje natural.

    :param segmento: Segmento SQL.
    :param client: Cliente de OpenAI.
    :return: Transcripción del segmento.
    """
    prompt = f"""
    Por favor, convierte el siguiente script SQL en una descripción detallada en lenguaje natural con formato Markdown, siguiendo el formato especificado a continuación. La descripción debe ser clara y estructurada, incluyendo:

    La descripción incluirá:
    - **El nombre de la tabla en mayúsculas.**
    - **Descripción:** [Explicación general de la tabla]
    - **Campos:**
        - **[Nombre del campo] ([Tipo de dato]):** [Explicación del campo]
    - **Relaciones:**
        - [Detalles de las relaciones, incluyendo llaves foráneas]

    Formato de la descripción:
    **[NOMBRE DE LA TABLA EN MAYÚSCULAS]**
    - **Descripción:** [Explicación general de la tabla]
    - **Campos:**
        - **[Nombre del campo] ([Tipo de dato]):** [Explicación del campo]
    - **Relaciones:**
        - [Detalles de las relaciones, incluyendo llaves foráneas]

    Ejemplo:
    Dado el siguiente script SQL:
    CREATE TABLE Usuarios (
        id_usuario INT PRIMARY KEY,
        nombre VARCHAR(100),
        email VARCHAR(100) UNIQUE,
        id_rol INT,
        FOREIGN KEY (id_rol) REFERENCES Roles(id_rol)
    );

    La transcripción sería:
    **USUARIOS**
    - **Descripción:** Esta tabla guarda información de los usuarios.
    - **Campos:**
        - **id_usuario (INT):** Identificador único de cada usuario, sirve como clave primaria.
        - **nombre (VARCHAR(100)):** Nombre del usuario.
        - **email (VARCHAR(100)):** Correo electrónico del usuario, debe ser único.
        - **id_rol (INT):** Identificador del rol del usuario, es una clave foránea que referencia a la tabla ROLES.
    - **Relaciones:**
        - Existe una relación con la tabla ROLES a través del campo id_rol.

    Ahora, por favor transcribe el siguiente script SQL siguiendo este formato:
    {segmento}
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2048  
    )
    return response.choices[0].message.content.strip() if response.choices else ''

def transcribir_sql_a_lenguaje_natural(archivo_sql, archivo_txt):
    dotenv.load_dotenv()
    client = OpenAI()
    client.api_key = os.environ.get('OPENAI_API_KEY')

    try:
        segmentos = segmentar_sql(archivo_sql)
        with open(archivo_txt, 'w', encoding='utf-8') as archivo_salida:
            for segmento in segmentos:
                transcripcion = transcribir_segmento(segmento, client)
                # Aquí puedes agregar lógica de postprocesamiento si es necesario
                archivo_salida.write(transcripcion + '\n\n--- Fin de Segmento ---\n\n')

        print(f"Archivo '{archivo_sql}' transcrito exitosamente a '{archivo_txt}'.")
    except Exception as e:
        print(f"Error al transcribir el archivo: {e}")

# Uso de la función
transcribir_sql_a_lenguaje_natural('./data/teams_actual.sql', './documents/markdown_database.md')
