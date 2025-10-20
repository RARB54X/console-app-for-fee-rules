import os
import pandas as pd
from simpleeval import simple_eval
from db.connection import get_db
from db.models import Agent, Transaction
import json
from pathlib import Path
from datetime import datetime

def save_results_json(results: list, output_dir: str = "output", prefix: str = "validations"):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.json"
    fullpath = out_path / filename
    with fullpath.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return str(fullpath)

def run_orchestrator(agent_ids: list[int], rules_excel_path: str = "excel/rules.xlsx"):
    """
    Ejecuta la validación de transacciones de los agentes especificados
    contra las reglas definidas en el archivo Excel.
    """
    if not os.path.exists(rules_excel_path):
        raise FileNotFoundError(f"No se encontró el archivo de reglas en: {rules_excel_path}")

    print(f"📘 Cargando reglas desde: {rules_excel_path}")
    df_rules = pd.read_excel(rules_excel_path)

    required_columns = {"rule_id", "description", "fields_required", "formula", "message_on_fail"}
    missing_cols = required_columns - set(df_rules.columns.str.lower())
    if missing_cols:
        raise ValueError(f"❌ El Excel de reglas no tiene las columnas requeridas: {missing_cols}")

    # Normaliza nombres de columnas para evitar errores por mayúsculas/minúsculas
    df_rules.columns = df_rules.columns.str.lower()

    results = []

    with get_db() as db:
        agents = db.query(Agent).filter(Agent.id.in_(agent_ids)).all()
        if not agents:
            print(f"⚠️ No se encontraron agentes con IDs: {agent_ids}")
            return []

        for agent in agents:
            print(f"\n🔍 Validando agente: {agent.name} (ID: {agent.id})")
            agent_result = {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "validations": []
            }

            transactions = db.query(Transaction).filter(Transaction.agent_id == agent.id).all()
            if not transactions:
                print(f"⚠️ No hay transacciones para el agente {agent.name}")
                continue

            for _, rule in df_rules.iterrows():
                rule_id = rule["rule_id"]
                description = rule["description"]
                formula = rule["formula"]
                fields_required = [f.strip() for f in str(rule["fields_required"]).split(",")]
                fail_message = rule.get("message_on_fail", "Validación fallida")

                print(f"➡️ Aplicando regla {rule_id}: {description}")

                for tx in transactions:
                    # Construir el contexto dinámicamente
                    context = {}
                    for field in fields_required:
                        if hasattr(tx, field):
                            context[field] = getattr(tx, field)
                        else:
                            context[field] = None  # Si falta el campo, se marca None

                    try:
                        result = simple_eval(formula, names=context)
                        agent_result["validations"].append({
                            "transaction_id": tx.id,
                            "rule_id": rule_id,
                            "ok": bool(result),
                            "message": "✅ OK" if result else f"❌ {fail_message}"
                        })
                    except Exception as e:
                        agent_result["validations"].append({
                            "transaction_id": tx.id,
                            "rule_id": rule_id,
                            "ok": False,
                            "message": f"⚠️ Error evaluando regla {rule_id}: {str(e)}"
                        })

            results.append(agent_result)

    print("\n🎯 Validación completada.")
    return results
