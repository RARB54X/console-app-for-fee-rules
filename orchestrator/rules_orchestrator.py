import pandas as pd
from simpleeval import simple_eval
from db.connection import get_db
from db.models import Agent, Transaction

def run_orchestrator(agent_ids: list[int], rules_excel_path: str = "rules/rules.xlsx"):
    """
    Ejecuta la validación de transacciones de los agentes especificados
    contra las reglas definidas en el archivo Excel.
    """
    results = []

    df_rules = pd.read_excel(rules_excel_path)
    with get_db() as db:
        agents = db.query(Agent).filter(Agent.id.in_(agent_ids)).all()

        for agent in agents:
            agent_result = {"agent_id": agent.id, "agent_name": agent.name, "validations": []}

            transactions = db.query(Transaction).filter(Transaction.agent_id == agent.id).all()

            for _, rule in df_rules.iterrows():
                rule_id = rule["Regla_ID"]
                formula = rule["Formula"]
                descripcion = rule.get("Descripcion", "")

                for tx in transactions:
                    context = {
                        "fee_total": tx.fee_total,
                        "fee_maxi": tx.fee_maxi,
                        "fee_operacion": tx.fee_operacion,
                        "fee_proveedor": tx.fee_proveedor,
                        "monto_origen": tx.monto_origen,
                        "monto_destino": tx.monto_destino,
                    }

                    try:
                        result = simple_eval(formula, names=context)
                        agent_result["validations"].append({
                            "transaction_id": tx.id,
                            "rule_id": rule_id,
                            "ok": bool(result),
                            "message": "OK" if result else f"Falló regla {rule_id}: {descripcion}"
                        })
                    except Exception as e:
                        agent_result["validations"].append({
                            "transaction_id": tx.id,
                            "rule_id": rule_id,
                            "ok": False,
                            "message": f"Error en regla {rule_id}: {str(e)}"
                        })

            results.append(agent_result)
    return results
