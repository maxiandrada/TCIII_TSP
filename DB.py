import sqlite3
from sqlite3 import Error

def create_connection(db_file):

    conn = None
    try:
        conn = sqlite3.connect(db_file,check_same_thread=False)
        return conn
    except Error as e:
        print(e)

    return conn

def DB():
    database = r"baseDeDatos.db"

    sql_sets_table = """CREATE TABLE IF NOT EXISTS Sets (
                        setId integer  PRIMARY KEY AUTOINCREMENT,
                        setName text NOT NULL
                        
                        );"""

    sql_instancias_table =   """CREATE TABLE IF NOT EXISTS Instancias (
                                instanciaId integer PRIMARY KEY AUTOINCREMENT,
                                instanciaName text NOT NULL,
                                cantidadNodos integer NOT NULL,
                                optimoConocido real,
                                coordenadas text NOT NULL
                            );"""

    sql_resoluciones_table = """CREATE TABLE IF NOT EXISTS Resoluciones (
                                resolucionId integer PRIMARY KEY AUTOINCREMENT,
                                iteraciones integer NOT NULL,
                                optimoEncontrado real NOT NULL,
                                tenueADD integer NOT NULL,
                                tenureDROP integer NOT NULL,
                                porcentajeError real NOT NULL,
                                tiempoResolucion real NOT NULL,
                                swaps text NOT NULL,
                                solucionInicial text NOT NULL,
                                criterioTenure integer NOT NULL
                            );"""

    sql_solucion_table = """CREATE TABLE IF NOT EXISTS Soluciones (
                            solucionId integer PRIMARY KEY AUTOINCREMENT,
                            costo float NOT NULL,
                            rutas text NOT NULL,
                            origen  text NOT NULL,
                            iteracion integer NOT null,
                            costoRutas text NOT null
                            );
                        """


    sql_instanciasXset_table = """CREATE TABLE IF NOT EXISTS InstanciasXSet (
                                    instanciaId integer NOT NULL,
                                    setId integer NOT NULL,
                                    PRIMARY KEY(instanciaId,setId),
                                    FOREIGN KEY (instanciaId) REFERENCES Instancia (instanciaId),
                                    FOREIGN KEY (setId) REFERENCES Sets (setId)
                                );"""

    sql_resolucionesXinstancia_table = """CREATE TABLE IF NOT EXISTS resolucionesXInstancia (
                                            instanciaId integer NOT NULL,
                                            resolucionId integer NOT NULL,
                                            PRIMARY KEY(instanciaId,resolucionId),
                                            FOREIGN KEY (resolucionId) REFERENCES Resoluciones (resolucionId),
                                            FOREIGN KEY (instanciaId) REFERENCES Instancias (instanciaId)
                                        );"""

    sql_solucionXresolucion_table = """CREATE TABLE IF NOT EXISTS solucionXresolucion (
                                            resolucionId integer NOT NULL,
                                            solucionId integer NOT NULL,
                                            PRIMARY KEY(solucionId,resolucionId),
                                            FOREIGN KEY (resolucionId) REFERENCES Resoluciones (resolucionId),
                                            FOREIGN KEY (solucionId) REFERENCES Soluciones (solucionId)
                                        );"""
    

    # crear conexión con base de datos
    conn = create_connection(database)

    # create tables
    if conn is not None:
        create_table(conn, sql_sets_table)
        create_table(conn, sql_instancias_table)
        create_table(conn, sql_resoluciones_table)
        create_table(conn, sql_solucion_table)
        create_table(conn, sql_resolucionesXinstancia_table)
        create_table(conn, sql_instanciasXset_table)
        create_table(conn, sql_solucionXresolucion_table)
    else:
        print("Error no se puede conectar a la base de datos")

    return conn

def create_table(conn, create_table_sql):

    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def insert_set(conn,_set):
    sql = ''' INSERT INTO Sets (setName) VALUES (?) '''

    cur = conn.cursor()
    cur.execute(sql, _set)
    conn.commit()

    return cur.lastrowid

def insert_resolucion(conn,resolucion):
    sql = ''' INSERT INTO Resoluciones (iteraciones,
                                        optimoEncontrado,
                                        tenueADD,tenureDROP,
                                        porcentajeError,
                                        tiempoResolucion,
                                        swaps,
                                        solucionInicial,
                                        criterioTenure) VALUES (?,?,?,?,?,?,?,?,?) '''

    cur = conn.cursor()
    cur.execute(sql, resolucion)
    conn.commit()

    return cur.lastrowid

def insert_resolucionXInstancia(conn, resXinst):
    sql = ''' INSERT INTO ResolucionesXInstancia (resolucionId,instanciaId) VALUES (?,?) '''
    cur = conn.cursor()
    cur.execute(sql, resXinst)
    conn.commit()
    return cur.lastrowid


def insert_instancia(conn,instancia):
    sql = ''' INSERT INTO Instancias (instanciaName,cantidadClientes,optimoConocido,coordenadas) VALUES (?,?,?,?) '''
    cur = conn.cursor()

    cur.execute(sql, instancia)
    conn.commit()

    return cur.lastrowid

def insert_solucion(conn, solucion):
    sql = ''' INSERT INTO Soluciones (costo, rutas, origen, iteracion, costoRutas) VALUES (?,?,?,?,?) '''
    cur = conn.cursor()

    cur.execute(sql, solucion)
    conn.commit()

    return cur.lastrowid

def insert_solucionXResolucion(conn, solucionXresolucion):
    sql = ''' INSERT INTO solucionXresolucion (resolucionId,solucionId) VALUES (?,?) '''
    cur = conn.cursor()
    cur.execute(sql, solucionXresolucion)
    conn.commit()

    return cur.lastrowid

def insert_instanciaXSet(conn, InstanciaXSet):
    sql = ''' INSERT INTO InstanciasXSet (instanciaId,setId) VALUES (?,?) '''
    cur = conn.cursor()
    cur.execute(sql, InstanciaXSet)
    conn.commit()

    return cur.lastrowid


##SELECT'S
def select_instancia(conn, instanciaId):
    sql =   f'''select *
                from Instancias
                WHERE instanciaId = {instanciaId}'''
    cur = conn.cursor()
    cur.execute(sql)
    filas = cur.fetchall()
    return filas



def select_instanciaCompletaXSet(conn, setId):
    sql =   f'''SELECT *
                FROM Instancias 
                INNER JOIN InstanciasXSet ON InstanciasXSet.instanciaId = Instancias.instanciaId
                WHERE setId = {setId}'''
    cur = conn.cursor()
    cur.execute(sql)
    filas = cur.fetchall()
    return filas



def select_instanciaXSet(conn, setId):
    """Solo consulta los datos 'simples' de la instancia, no incluye la matriz ni las demandas"""
    sql =   f'''select Instancias.instanciaId,instanciaName,cantidadClientes,nroVehiculos,capacidad,optimoConocido
                from Instancias INNER  JOIN InstanciasXSet ON InstanciasXSet.instanciaId = Instancias.instanciaId
                WHERE setId = {setId}'''
    cur = conn.cursor()
    cur.execute(sql)
    filas = cur.fetchall()
    return filas

def select_sets(conn):
    sql = """select * from Sets """
    cur = conn.cursor()
    cur.execute(sql)
    filas = cur.fetchall()
    return filas
   
def select_sets_con_nombre(conn, nombre):
    sql = f"SELECT * FROM Sets WHERE setName='{nombre}'"
    cur = conn.cursor()
    cur.execute(sql)
    filas = cur.fetchall()
    return filas

def select_soluciones(conn, solucionId=None):
    if solucionId is None:
        sql = """select * from Soluciones"""
    else:
        sql = f"select * from Soluciones where solucionId = {solucionId}"
    cur = conn.cursor()
    cur.execute(sql)
    filas = cur.fetchall()
    return filas

def select_solucionesXResolucion(conn, resolucionId):
    sql = f'''select Soluciones.solucionId,costo,rutas,origen,iteracion
            from Soluciones INNER JOIN solucionXresolucion ON solucionXresolucion.solucionId = Soluciones.solucionId
            WHERE resolucionId = {resolucionId}'''
    cur = conn.cursor()
    cur.execute(sql)
    filas = cur.fetchall()
    return filas

def selectSwapsInstancia(conn, instanciaId):
    sql = f"""
    select swaps from Resoluciones INNER JOIN resolucionesXInstancia     
    ON resolucionesXInstancia.resolucionId = Resoluciones.resolucionId  
    INNER JOIN Instancias                                               
    ON resolucionesXInstancia.instanciaId = Instancias.instanciaId  
    WHERE Instancias.instanciaId = {instanciaId}"""                           
    cur = conn.cursor()
    cur.execute(sql)
    filas = cur.fetchall()
    return filas

def select_resoluciones(conn, resolucionId=None):
    if resolucionId is None:
        sql = """select * from Resoluciones"""
    else:
        sql = f"select * from Resoluciones where resolucionId = {resolucionId}"
    cur = conn.cursor()
    cur.execute(sql)
    filas = cur.fetchall()
    return filas

def select_resolucionesXInstancia(conn,instanciaId):
    sql =   f'''select Resoluciones.resolucionId,iteraciones,optimoEncontrado,tenueADD,tenureDROP,porcentajeError,tiempoResolucion,swaps,solucionInicial
            from Resoluciones INNER  JOIN resolucionesXInstancia ON resolucionesXInstancia.resolucionId = Resoluciones.resolucionId
            WHERE instanciaId = {instanciaId}'''
    cur = conn.cursor()
    cur.execute(sql)
    filas = cur.fetchall()
    return filas

def select_reporte_total(conn, instanciaId):
    sql = """
        SELECT
            instanciaName,
            AVG(optimoEncontrado),
            MIN(optimoEncontrado),
            optimoConocido,
            AVG(porcentajeError),
            COUNT(*)
        FROM
            Instancias INNER JOIN resolucionesXInstancia
            ON Instancias.instanciaId = resolucionesXInstancia.instanciaId
            INNER JOIN Resoluciones
            ON resolucionesXInstancia.resolucionId = Resoluciones.resolucionId
        WHERE
            Instancias.instanciaId = %s
        GROUP BY
            instanciaName
        """%instanciaId
    cur = conn.cursor()
    cur.execute(sql)
    filas = cur.fetchall()
    return filas


if  __name__ == '__main__':
    DB()
