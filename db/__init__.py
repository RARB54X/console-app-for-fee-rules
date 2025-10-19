"""
Paquete de conexión y modelos de base de datos.
Incluye:
- connection.py: configuración SQLAlchemy
- models.py: definición de tablas
- seed_data.py: carga inicial de datos dummy
"""

from .connection import Base, engine, get_db, create_all_tables
from .models import Agent, Transaction