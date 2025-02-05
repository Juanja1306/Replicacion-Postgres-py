Sincronización Bidireccional de Bases de Datos PostgreSQL
=========================================================

Este proyecto contiene un script en Python que permite sincronizar cambios entre dos bases de datos PostgreSQL de manera bidireccional. La sincronización se realiza leyendo los cambios registrados en una tabla especial ("database_changes") y aplicándolos en la otra base de datos. Se han implementado mecanismos de control de errores, reconexión y logs con colores para facilitar la monitorización.

---------------------------------------------------------
## Tabla de Contenidos

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Descripción del Código](#descripción-del-código)
- [Manejo de Errores y Logging](#manejo-de-errores-y-logging)


---------------------------------------------------------
## Características

- Sincronización bidireccional: Actualiza ambas bases de datos, transfiriendo los cambios de la primaria a la secundaria y viceversa.
- Uso de pool de conexiones: Se emplea "psycopg2.pool.SimpleConnectionPool" para gestionar múltiples conexiones de forma eficiente.
- Ejecución programada: El script utiliza el módulo "schedule" para ejecutar la sincronización de forma periódica (cada 5 segundos).
- Logs con colores: Con "colorama" se resaltan los mensajes en consola, facilitando la identificación de errores, advertencias e información.
- Manejo robusto de errores: Se implementa la verificación de la disponibilidad de las bases de datos y se gestionan excepciones durante la ejecución de consultas.

---------------------------------------------------------
## Requisitos

- Python 3.12 
- PostgreSQL 17

Dependencias de Python:
- psycopg2 (o psycopg2-binary)
- colorama
- schedule

---------------------------------------------------------
## Instalación

1. Clonar el repositorio o descargar el script:

   git clone https://tu-repositorio.git
   cd tu-repositorio

2. Crear un entorno virtual (opcional pero recomendado):

   python3 -m venv venv
   source venv/bin/activate   (en Windows: venv\Scripts\activate)

3. Instalar las dependencias:

   pip install psycopg2-binary colorama schedule

---------------------------------------------------------
## Configuración

El script establece dos pools de conexiones para las bases de datos primaria y secundaria. Las configuraciones actuales son:

Base de Datos Secundaria:
- Usuario: postgres
- Contraseña: 0000
- Host: 192.168.72.129
- Puerto: 5432
- Base de Datos: tolerancia_db

Base de Datos Primaria:
- Usuario: postgres
- Contraseña: 0000
- Host: 192.168.72.133
- Puerto: 5432
- Base de Datos: tolerancia_db

Nota: Si es necesario, edita los parámetros de conexión directamente en el script.

Adicionalmente, asegúrate de que ambas bases de datos cuenten con la tabla "database_changes", la cual debe incluir al menos las columnas:
- id
- metodo (con valores como INSERT, UPDATE o DELETE)
- tabla
- descripcion (en formato JSON o diccionario)

---------------------------------------------------------
## Uso

Para iniciar la sincronización, ejecuta el script con:

   python nombre_del_script.py

El proceso se ejecutará de manera continua, verificando y aplicando los cambios entre ambas bases de datos cada 5 segundos.

---------------------------------------------------------
## Descripción del Código

1. Conexión a las Bases de Datos
   - Se configuran dos pools de conexiones utilizando "psycopg2.pool.SimpleConnectionPool", uno para cada base de datos. Si ocurre algún error al crear los pools, se imprime un mensaje de error y se termina la ejecución.

2. Función "check_database_availability"
   - Verifica si una base de datos está disponible obteniendo una conexión desde el pool. Si falla, se muestra un mensaje y retorna False.

3. Función "build_query"
   - Construye la consulta SQL a ejecutar basándose en un registro de cambio. Dependiendo del valor de la clave "metodo", se genera una consulta para:
     * INSERT: Inserta nuevos registros.
     * UPDATE: Actualiza registros existentes.
     * DELETE: Elimina registros.
   - La columna "descripcion" se parsea (en formato JSON o diccionario) para obtener los datos necesarios.

4. Función "sync_changes"
   - Realiza la sincronización de los cambios desde una base de datos origen a una destino:
     a. Verifica la disponibilidad de ambas bases de datos.
     b. Lee los registros de la tabla "database_changes" ordenados por "id".
     c. Para cada registro:
        - Construye la consulta SQL con "build_query".
        - Ejecuta la consulta en la base de datos destino.
        - Si se ejecuta correctamente, elimina el registro de la tabla de cambios en la base de datos origen.
     d. Maneja los errores de conexión y otros posibles errores de ejecución.

5. Función "job"
   - Función principal que coordina la sincronización en ambas direcciones:
     * De la base de datos primaria a la secundaria.
     * De la base de datos secundaria a la primaria.

6. Ejecución Programada
   - El módulo "schedule" programa la ejecución de la función "job" cada 5 segundos. Un bucle infinito se encarga de mantener el proceso activo, ejecutando las tareas programadas.

---------------------------------------------------------
## Manejo de Errores y Logging

- Conexión: Se verifica la disponibilidad de cada base de datos antes de intentar la sincronización.
- Ejecución de consultas: Se captura y maneja cualquier excepción durante la ejecución de las consultas SQL.
- Mensajes de Log: Utiliza "colorama" para imprimir:
  * Rojo: Errores críticos (p. ej., fallo en la creación de pools o errores durante la ejecución de una consulta).
  * Amarillo: Advertencias y estados de standby ante problemas de conexión.
  * Cian, Azul y Verde: Mensajes informativos sobre el proceso de sincronización.
