from .connection import get_db, create_all_tables
from .models import Agent, Transaction
import random

def seed_data():
    create_all_tables()
    with get_db() as db:
        if db.query(Agent).count() == 0:
            print("→ Insertando datos dummy...")

            agents = [Agent(name=f"Agente {i}") for i in range(1, 4)]
            db.add_all(agents)
            db.flush()  # para obtener IDs

            for agent in agents:
                for _ in range(5):  # 5 transacciones por agente
                    fee_maxi = random.uniform(0.5, 2)
                    fee_operacion = random.uniform(0.2, 1)
                    fee_proveedor = random.uniform(0.1, 0.5)
                    fee_total = fee_maxi + fee_operacion + fee_proveedor

                    tx = Transaction(
                        agent_id=agent.id,
                        origen="USD",
                        destino="COP",
                        monto_origen=random.uniform(50, 200),
                        monto_destino=random.uniform(200000, 900000),
                        fee_total=fee_total,
                        fee_maxi=fee_maxi,
                        fee_operacion=fee_operacion,
                        fee_proveedor=fee_proveedor,
                    )
                    db.add(tx)
            print("✓ Datos dummy insertados correctamente.")
        else:
            print("⚠️ Ya existen datos en la base de datos.")
