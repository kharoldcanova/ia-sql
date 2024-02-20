from openai import OpenAI
import dotenv
import os

def transcribir_sql_a_lenguaje_natural(archivo_sql, archivo_txt, tamano_del_segmento=2048):
    """
    Transcribe un archivo SQL a lenguaje natural por partes.

    :param archivo_sql: Ruta del archivo SQL de entrada.
    :param archivo_txt: Ruta del archivo .txt de salida.
    :param tamano_del_segmento: Tamaño del segmento en bytes.
    """

    dotenv.load_dotenv()
    client = OpenAI()
    client.api_key = os.environ.get('OPENAI_API_KEY')

    try:
        with open(archivo_sql, 'r', encoding='utf-8') as archivo_entrada:
            with open(archivo_txt, 'w', encoding='utf-8') as archivo_salida:
                while True:
                    sql_content = archivo_entrada.read(tamano_del_segmento)
                    if not sql_content:
                        break

                    prompt = f"""
                        Por favor, convierte el siguiente script SQL en una descripción detallada en lenguaje natural. La descripción debe incluir:
                        - Nombre de cada tabla.
                        - Descripción general de para qué se usa la tabla.
                        - Listado de campos con su tipo de dato y una breve descripción de cada campo.
                        - Relaciones con otras tablas si las hay.

                        Ejemplo de lo que busco:
                        Si el script SQL es:
                        CREATE TABLE Usuarios (
                            id_usuario INT PRIMARY KEY,
                            nombre VARCHAR(100),
                            email VARCHAR(100) UNIQUE
                        );

                        La descripción debe ser:
                        Tabla: Usuarios
                        Descripción: Esta tabla almacena información de los usuarios.
                        Campos:
                            - id_usuario (INT): Identificador único para cada usuario. Es la clave primaria de la tabla.
                            - nombre (VARCHAR(100)): Nombre del usuario.
                            - email (VARCHAR(100)): Dirección de correo electrónico del usuario. Debe ser única.

                        Ahora, por favor transcribe el siguiente script SQL siguiendo este formato:
                        {sql_content}
                        """

                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=2048  
                    )

                    # Ajuste en la forma de acceder a la respuesta
                    if response.choices:
                        message_content = response.choices[0].message.content
                        archivo_salida.write(message_content.strip() + '\n\n--- Fin de Segmento ---\n\n')

        print(f"Archivo '{archivo_sql}' transcrito exitosamente a '{archivo_txt}'.")
    except Exception as e:
        print(f"Error al transcribir el archivo: {e}")

# Uso de la función
transcribir_sql_a_lenguaje_natural('./data/teams.sql', './data/documentation_version_1.txt')

