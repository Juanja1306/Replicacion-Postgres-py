import psycopg2
from psycopg2 import pool, OperationalError
import json
import time
import schedule
from colorama import Fore, Back, Style, init

# Inicializamos colorama
init(autoreset=True)

# Configuración de conexiones a ambas bases de datos usando un pool de conexiones
try:
    secondary_db_pool = psycopg2.pool.SimpleConnectionPool(
        1, 10,
        user="postgres",
        password="0000",
        host="192.168.72.129",  # IP de la base de datos secundaria
        port="5432",
        database="tolerancia_db"
    )
    primary_db_pool = psycopg2.pool.SimpleConnectionPool(
        1, 10,
        user="postgres",
        password="0000",
        host="192.168.72.133",  # IP de la base de datos primaria
        port="5432",
        database="tolerancia_db"
    )
except Exception as e:
    print(Back.RED + f"Error al crear los pools de conexión: {e}")
    exit(1)


def check_database_availability(db_pool: pool.SimpleConnectionPool, db_name: str) -> bool:
    """
    Verifica si la base de datos está disponible obteniendo una conexión del pool.
    Si la conexión falla, se imprime un mensaje y se retorna False.
    """
    try:
        conn = db_pool.getconn()
        db_pool.putconn(conn)
        return True
    except Exception as e:
        print(Back.RED + f"Máquina {db_name} no se encuentra disponible: {e}")
        return False


def build_query(change: dict) -> str:
    """
    Construye la consulta SQL a partir del registro 'change'.
    Se espera que 'change' tenga las claves: 'id', 'metodo', 'tabla' y 'descripcion'.
    """
    data = None
    try:
        if isinstance(change.get('descripcion'), dict):
            data = change.get('descripcion')
        else:
            data = json.loads(change.get('descripcion'))
    except Exception as e:
        print(Back.RED + f"Error al parsear JSON en {change.get('tabla')}: {e}")
        return ''
    
    query = ''
    metodo = change.get('metodo')
    tabla = change.get('tabla')

    if metodo == 'INSERT':
        columns = ', '.join(data.keys())
        # Colocamos cada valor entre comillas
        values = ', '.join(f"'{v}'" for v in data.values())
        query = f"INSERT INTO {tabla} ({columns}) VALUES ({values});"
    elif metodo == 'UPDATE':
        set_values = ', '.join(f"{k} = '{v}'" for k, v in data.items())
        query = f"UPDATE {tabla} SET {set_values} WHERE id = '{data.get('id')}';"
    elif metodo == 'DELETE':
        query = f"DELETE FROM {tabla} WHERE id = '{data.get('id')}';"
    
    return query


def sync_changes(source_db_pool: pool.SimpleConnectionPool, target_db_pool: pool.SimpleConnectionPool,
                 source_name: str, target_name: str) -> None:
    """
    Sincroniza los cambios registrados en la tabla "database_changes" de la base de datos origen
    hacia la base de datos destino. Si ocurre un error de conexión (por ejemplo, la base se desconecta),
    se notifica y se abandona la sincronización para ese ciclo, esperando que en el próximo se recupere la conexión.
    """
    # Verificar disponibilidad antes de proceder
    if not check_database_availability(source_db_pool, source_name):
        print(Fore.YELLOW + f"{source_name} desconectada. Quedando en standby hasta reconexión.")
        return
    if not check_database_availability(target_db_pool, target_name):
        print(Fore.YELLOW + f"{target_name} desconectada. Quedando en standby hasta reconexión.")
        return

    print(Fore.CYAN + Style.BRIGHT + f"Sincronizando desde {source_name} a {target_name}...")
    
    try:
        source_conn = source_db_pool.getconn()
        source_cursor = source_conn.cursor()
    except OperationalError as e:
        print(Fore.YELLOW + f"{source_name} no disponible: {e}. Quedando en standby.")
        return
    except Exception as e:
        print(Back.RED + f"Error conectando a {source_name}: {e}")
        return

    try:
        source_cursor.execute('SELECT * FROM "database_changes" ORDER BY id ASC')
        rows = source_cursor.fetchall()

        if not rows:
            print(Fore.LIGHTBLACK_EX + f"Sin cambios en {source_name}.\n")
            return

        # Obtener los nombres de las columnas para convertir cada fila en un diccionario
        col_names = [desc[0] for desc in source_cursor.description]

        for row in rows:
            change = dict(zip(col_names, row))
            sql_query = build_query(change)
            if not sql_query:
                print(Fore.RED + f"Saltando fila con error en JSON en {source_name}")
                continue

            print(Fore.YELLOW + f"Ejecutando en {target_name}: {sql_query}")
            try:
                target_conn = target_db_pool.getconn()
                target_cursor = target_conn.cursor()
                target_cursor.execute(sql_query)
                target_conn.commit()
                target_cursor.close()
                target_db_pool.putconn(target_conn)
            except OperationalError as e:
                # Capturamos errores de conexión durante la ejecución del query
                print(Fore.YELLOW + f"Error en conexión con {target_name}: {e}. Quedando en standby.")
                return
            except Exception as e:
                print(Back.RED + f"Error ejecutando query en {target_name}: {e}")
                # Se podría agregar un rollback o lógica adicional si fuera necesario

            # Eliminar la fila procesada de la base de datos origen
            try:
                source_cursor.execute('DELETE FROM "database_changes" WHERE id = %s', (change.get('id'),))
                source_conn.commit()
            except Exception as e:
                print(Back.RED + f"Error eliminando el registro en {source_name}: {e}")

        print(Fore.GREEN + Style.BRIGHT + f"Sincronización de {source_name} a {target_name} completa.")

    except OperationalError as e:
        print(Fore.YELLOW + f"Error en conexión durante sincronización desde {source_name} a {target_name}: {e}")
    except Exception as e:
        print(Back.RED + f"Error sincronizando de {source_name} a {target_name}: {e}")
    finally:
        try:
            source_cursor.close()
            source_db_pool.putconn(source_conn)
        except Exception:
            pass


def job():
    """
    Función que ejecuta la sincronización en ambas direcciones.
    """
    print(Fore.BLUE + "Iniciando sincronización...")
    sync_changes(primary_db_pool, secondary_db_pool, 'PrimaryDB', 'SecondaryDB')
    sync_changes(secondary_db_pool, primary_db_pool, 'SecondaryDB', 'PrimaryDB')
    print(Fore.MAGENTA + "Sincronización finalizada.\n")


# Programar la ejecución cada 5 segundos
schedule.every(5).seconds.do(job)

if __name__ == '__main__':
    while True:
        schedule.run_pending()
        time.sleep(1)
