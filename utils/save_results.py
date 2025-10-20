import json
import os
from datetime import datetime

def save_results_json(results, output_dir="output", prefix="validations"):
    """Guarda los resultados del orquestador en un archivo JSON con timestamp."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(output_dir, f"{prefix}_{timestamp}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return file_path
