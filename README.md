# Sincronización Bidireccional de Bases de Datos PostgreSQL

Este proyecto contiene un script en Python que permite sincronizar cambios entre dos bases de datos PostgreSQL de manera bidireccional. La sincronización se realiza leyendo los cambios registrados en una tabla especial (`database_changes`) y aplicándolos en la otra base de datos. Se han implementado mecanismos de control de errores, reconexión y logs con colores para facilitar la monitorización.

---

## Tabla de Contenidos

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Descripción del Código](#descripción-del-código)
- [Manejo de Errores y Logging](#manejo-de-errores-y-logging)
- [Licencia](#licencia)

---

## Características

- **Sincronización bidireccional:** Actualiza ambas bases de datos, transfiriendo los cambios de la primaria a la secundaria y viceversa.
- **Uso de pool de conexiones:** Se emplea `psycopg2.pool.SimpleConnectionPool` para gestionar múltiples conexiones de forma eficiente.
- **Ejecución programada:** El script utiliza el módulo `schedule` para ejecutar la sincronización de forma periódica (cada 5 segundos).
- **Logs con colores:** Con `colorama` se resaltan los mensajes en consola, facilitando la identificación de errores, advertencias e información.
- **Manejo robusto de errores:** Se implementa la verificación de la disponibilidad de las bases de datos y se gestionan excepciones durante la ejecución de consultas.

---

## Requisitos

- **Python 3.6+**
- **PostgreSQL**

### Dependencias de Python

- `psycopg2` (o `psycopg2-binary`)
- `colorama`
- `schedule`

---

## Instalación

1. **Clonar el repositorio o descargar el script:**

   ```bash
   git clone https://tu-repositorio.git
   cd tu-repositorio
