import argparse
from db.connection import test_connection, get_table_names, create_all_tables
from db.seed_data import seed_data
from orchestrator.rules_orchestrator import run_orchestrator
from db.models import Agent, Transaction


def main():
    parser = argparse.ArgumentParser(description="Validador de transacciones por agente.")
    parser.add_argument("--agents", nargs="+", type=int, help="IDs de agentes a validar")
    parser.add_argument("--seed", action="store_true", help="Insertar datos dummy")
    parser.add_argument("--test-db", action="store_true", help="Probar conexión a BD")

    args = parser.parse_args()

    # ------------------------------------------
    # Opción: probar conexión a la base de datos
    # ------------------------------------------
    if args.test_db:
        if test_connection():
            print("\n📋 Tablas actuales:")
            tables = get_table_names()
            for t in tables:
                print(f"  - {t}")
        return

    # ------------------------------------------
    # Opción: insertar datos dummy
    # ------------------------------------------
    if args.seed:
        print("🚀 Creando tablas y sembrando datos dummy...")
        create_all_tables()  # 👈 esto garantiza que 'agents' y 'transactions' existan
        seed_data()
        print("✅ Datos dummy insertados correctamente.")
        return

    # ------------------------------------------
    # Opción: ejecutar el orquestador por agentes
    # ------------------------------------------
    if args.agents:
        print(f"🔍 Ejecutando validación para agentes: {args.agents}")
        run_orchestrator(args.agents)
        return

    # ------------------------------------------
    # Si no se pasa ningún argumento
    # ------------------------------------------
    parser.print_help()


if __name__ == "__main__":
    main()
