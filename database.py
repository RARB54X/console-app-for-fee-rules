from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from urllib.parse import quote_plus
from contextlib import contextmanager
from typing import Generator
from dotenv import load_dotenv
import os

# =====================================================
# CARGAR VARIABLES DE ENTORNO
# =====================================================

# Cargar el archivo .env
load_dotenv()

# =====================================================
# CONFIGURACIÓN DE LA BASE DE DATOS DESDE .ENV
# =====================================================

SERVER = os.getenv('DB_SERVER', r'DESKTOP-GN14PVG\SQLEXPRESS')
DATABASE = os.getenv('DB_NAME', 'TestDB')
DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
AUTH_TYPE = os.getenv('DB_AUTH_TYPE', 'windows').lower()

# Credenciales SQL Server (solo si usas SQL Authentication)
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Configuración del engine desde .env
ECHO = os.getenv('DB_ECHO', 'False').lower() == 'true'
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '20'))
POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))

# =====================================================
# CADENA DE CONEXIÓN
# =====================================================

def get_connection_string():
    """
    Genera la cadena de conexión para SQL Server.
    Soporta Windows Authentication y SQL Server Authentication.
    
    Returns:
        str: Cadena de conexión completa
    """
    if AUTH_TYPE == 'windows':
        # Windows Authentication
        connection_string = (
            f'mssql+pyodbc://{SERVER}/{DATABASE}'
            f'?driver={quote_plus(DRIVER)}'
            f'&trusted_connection=yes'
        )
    else:
        # SQL Server Authentication
        if not DB_USERNAME or not DB_PASSWORD:
            raise ValueError(
                "Para SQL Authentication debes configurar DB_USERNAME y DB_PASSWORD en .env"
            )
        connection_string = (
            f'mssql+pyodbc://{DB_USERNAME}:{quote_plus(DB_PASSWORD)}'
            f'@{SERVER}/{DATABASE}'
            f'?driver={quote_plus(DRIVER)}'
        )
    
    return connection_string

# =====================================================
# CREAR ENGINE
# =====================================================

ENGINE_CONFIG = {
    'echo': ECHO,
    'pool_pre_ping': True,
    'pool_size': POOL_SIZE,
    'max_overflow': MAX_OVERFLOW,
    'pool_recycle': POOL_RECYCLE,
}

engine = create_engine(
    get_connection_string(),
    **ENGINE_CONFIG
)

# =====================================================
# BASE PARA MODELOS
# =====================================================

Base = declarative_base()

# =====================================================
# CONFIGURACIÓN DE SESIONES
# =====================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# =====================================================
# FUNCIONES DE SESIÓN
# =====================================================

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager para obtener sesiones de base de datos.
    Maneja automáticamente commit, rollback y cierre de sesión.
    
    Ejemplo:
        with get_db() as db:
            usuario = db.query(Usuario).filter_by(id=1).first()
            usuario.nombre = "Nuevo nombre"
            # Commit automático al salir del with si no hay errores
    
    Yields:
        Session: Sesión de SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_dependency() -> Generator[Session, None, None]:
    """
    Generador para dependency injection (FastAPI, etc).
    NO hace commit automático - el usuario debe manejar las transacciones.
    
    Ejemplo en FastAPI:
        @app.get("/usuarios")
        def obtener_usuarios(db: Session = Depends(get_db_dependency)):
            return db.query(Usuario).all()
    
    Yields:
        Session: Sesión de SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_simple() -> Session:
    """
    Obtiene una sesión simple sin context manager.
    ⚠️ IMPORTANTE: Debes cerrar manualmente la sesión con db.close()
    
    Returns:
        Session: Sesión de SQLAlchemy
    """
    return SessionLocal()

# =====================================================
# FUNCIONES AUXILIARES
# =====================================================

def test_connection():
    """
    Prueba la conexión a la base de datos
    
    Returns:
        bool: True si la conexión es exitosa, False en caso contrario
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT @@VERSION"))
            version = result.fetchone()
            print("✓ Conexión exitosa a SQL Server")
            print(f"✓ Base de datos: {DATABASE}")
            print(f"✓ Servidor: {SERVER}")
            print(f"✓ Autenticación: {AUTH_TYPE.upper()}")
            print(f"✓ Versión SQL Server: {version[0][:80]}...")
            
            result = connection.execute(text("SELECT SYSTEM_USER, CURRENT_USER"))
            user_info = result.fetchone()
            print(f"✓ Usuario conectado: {user_info[0]}")
            
            return True
    except Exception as e:
        print(f"✗ Error de conexión: {e}")
        print("\n🔍 Verificaciones:")
        print("  1. SQL Server está ejecutándose")
        print("  2. Las credenciales en .env son correctas")
        print("  3. La base de datos existe")
        print(f"  4. Driver ODBC instalado: {DRIVER}")
        print(f"  5. Servidor accesible: {SERVER}")
        
        if AUTH_TYPE == 'windows':
            print("\n💡 Windows Authentication:")
            print("   - Tu usuario de Windows debe tener permisos en SQL Server")
            print("   - Verifica en SSMS: Security > Logins")
        else:
            print("\n💡 SQL Server Authentication:")
            print("   - Verifica DB_USERNAME y DB_PASSWORD en .env")
            print("   - El usuario SQL debe existir y tener permisos")
        
        return False

def create_all_tables():
    """
    Crea todas las tablas definidas en los modelos
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Todas las tablas fueron creadas exitosamente")
        return True
    except Exception as e:
        print(f"✗ Error al crear tablas: {e}")
        return False

def drop_all_tables():
    """
    Elimina todas las tablas (¡CUIDADO! Uso solo en desarrollo)
    """
    try:
        environment = os.getenv('ENVIRONMENT', 'development')
        if environment == 'production':
            print("❌ PROHIBIDO eliminar tablas en producción")
            return False
            
        respuesta = input("⚠️  ¿Estás SEGURO de eliminar todas las tablas? (SI/no): ")
        if respuesta.upper() == "SI":
            Base.metadata.drop_all(bind=engine)
            print("✓ Todas las tablas fueron eliminadas")
            return True
        else:
            print("✗ Operación cancelada")
            return False
    except Exception as e:
        print(f"✗ Error al eliminar tablas: {e}")
        return False

def get_table_names():
    """
    Obtiene la lista de tablas en la base de datos
    
    Returns:
        list: Lista de nombres de tablas
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """))
            tables = [row[0] for row in result]
            return tables
    except Exception as e:
        print(f"✗ Error al obtener tablas: {e}")
        return []

def show_connection_info():
    """
    Muestra información de la configuración de conexión
    """
    print("\n" + "="*60)
    print("  INFORMACIÓN DE CONEXIÓN A BASE DE DATOS")
    print("="*60)
    print(f"Servidor: {SERVER}")
    print(f"Base de datos: {DATABASE}")
    print(f"Driver: {DRIVER}")
    print(f"Autenticación: {AUTH_TYPE.upper()}")
    
    if AUTH_TYPE == 'sql':
        print(f"Usuario SQL: {DB_USERNAME}")
        print(f"Contraseña: {'*' * len(DB_PASSWORD) if DB_PASSWORD else 'NO CONFIGURADA'}")
    
    print(f"Pool size: {POOL_SIZE}")
    print(f"Max overflow: {MAX_OVERFLOW}")
    print(f"Echo SQL: {ECHO}")
    
    environment = os.getenv('ENVIRONMENT', 'unknown')
    print(f"Entorno: {environment.upper()}")
    print("="*60 + "\n")

def check_database_exists():
    """
    Verifica si la base de datos existe
    
    Returns:
        bool: True si existe, False si no existe
    """
    try:
        if AUTH_TYPE == 'windows':
            temp_connection_string = (
                f'mssql+pyodbc://{SERVER}/master'
                f'?driver={quote_plus(DRIVER)}'
                f'&trusted_connection=yes'
            )
        else:
            temp_connection_string = (
                f'mssql+pyodbc://{DB_USERNAME}:{quote_plus(DB_PASSWORD)}'
                f'@{SERVER}/master'
                f'?driver={quote_plus(DRIVER)}'
            )
        
        temp_engine = create_engine(temp_connection_string)
        
        with temp_engine.connect() as connection:
            result = connection.execute(text(f"""
                SELECT database_id 
                FROM sys.databases 
                WHERE name = '{DATABASE}'
            """))
            exists = result.fetchone() is not None
            
            if exists:
                print(f"✓ La base de datos '{DATABASE}' existe")
            else:
                print(f"✗ La base de datos '{DATABASE}' NO existe")
                print(f"\n💡 Créala con SQL Server Management Studio o ejecutando:")
                print(f"   CREATE DATABASE [{DATABASE}]")
            
            return exists
            
    except Exception as e:
        print(f"✗ Error al verificar la base de datos: {e}")
        return False

def check_env_file():
    """
    Verifica que el archivo .env exista y tenga las variables necesarias
    
    Returns:
        bool: True si todo está correcto, False si falta algo
    """
    print("\n📋 Verificando archivo .env...")
    
    if not os.path.exists('.env'):
        print("❌ Archivo .env NO encontrado")
        print("\n💡 Crea un archivo .env con:")
        print("   DB_SERVER=tu_servidor")
        print("   DB_NAME=tu_base_de_datos")
        print("   DB_DRIVER=ODBC Driver 17 for SQL Server")
        print("   DB_AUTH_TYPE=windows")
        return False
    
    print("✓ Archivo .env encontrado")
    
    # Variables requeridas
    required_vars = ['DB_SERVER', 'DB_NAME', 'DB_DRIVER', 'DB_AUTH_TYPE']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    # Si usa SQL Auth, verificar credenciales
    if AUTH_TYPE == 'sql':
        if not DB_USERNAME:
            missing_vars.append('DB_USERNAME')
        if not DB_PASSWORD:
            missing_vars.append('DB_PASSWORD')
    
    if missing_vars:
        print(f"⚠️  Variables faltantes: {', '.join(missing_vars)}")
        return False
    
    print("✓ Todas las variables necesarias están configuradas")
    return True

# =====================================================
# EJEMPLOS DE USO
# =====================================================

def ejemplo_uso():
    """
    Ejemplos de cómo usar las diferentes funciones de sesión
    """
    print("\n" + "="*60)
    print("  EJEMPLOS DE USO DE SESIONES")
    print("="*60)
    
    print("\n1️⃣ USO RECOMENDADO - Context Manager (get_db):")
    print("""
    from database import get_db
    from models import Usuario
    
    with get_db() as db:
        usuario = Usuario(nombre="Juan", email="juan@example.com")
        db.add(usuario)
        # Commit automático aquí si no hay errores
    """)
    
    print("\n2️⃣ USO CON FASTAPI - Dependency Injection:")
    print("""
    from fastapi import FastAPI, Depends
    from sqlalchemy.orm import Session
    from database import get_db_dependency
    
    app = FastAPI()
    
    @app.get("/usuarios")
    def obtener_usuarios(db: Session = Depends(get_db_dependency)):
        return db.query(Usuario).all()
    """)
    
    print("="*60 + "\n")

# =====================================================
# INICIALIZACIÓN
# =====================================================

if __name__ == "__main__":
    """
    Ejecuta este archivo directamente para probar la conexión
    """
    print("\n🔍 Verificando configuración de base de datos...\n")
    
    # Verificar .env
    if not check_env_file():
        print("\n❌ Configuración incompleta. Revisa tu archivo .env")
        exit(1)
    
    show_connection_info()
    
    # Verificar base de datos
    print("📋 Verificando base de datos...")
    if not check_database_exists():
        print("\n⚠️  La base de datos no existe. Créala primero.")
    else:
        # Probar conexión
        if test_connection():
            print("\n📋 Tablas existentes:")
            tables = get_table_names()
            if tables:
                for i, table in enumerate(tables, 1):
                    print(f"  {i}. {table}")
            else:
                print("  No hay tablas en la base de datos")
            
            ejemplo_uso()
        else:
            print("\n❌ No se pudo conectar a la base de datos")