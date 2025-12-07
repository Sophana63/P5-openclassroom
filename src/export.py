# export_patients.py

from pymongo import MongoClient
from pymongo.collection import Collection
import pandas as pd
import json
from pathlib import Path
from connection import MongoDBConnection

# Fonction de conversion pour JSON
def convert_doc(doc):
    doc_copy = doc.copy()
    
    # _id n’est pas JSON serializable → le convertir en str
    if "_id" in doc_copy:
        doc_copy["_id"] = str(doc_copy["_id"])
    
    # Convertir les dates en string YYYY-MM-DD
    for key in ["Date of Admission", "Discharge Date"]:
        if key in doc_copy and hasattr(doc_copy[key], "strftime"):
            doc_copy[key] = doc_copy[key].strftime("%Y-%m-%d")
    
    return doc_copy

# Créer le dossier de sortie si inexistant
output_dir = Path("data")
output_dir.mkdir(exist_ok=True)

# Export JSON
def export_json(collection: Collection):
    data = list(collection.find())
    data_clean = [convert_doc(d) for d in data]
    output_file = "data/collection.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data_clean, f, ensure_ascii=False, indent=4)
    print(f"✅ Export JSON terminé : {output_file}")


# Export CSV
def export_csv(collection: Collection):
    data = list(collection.find())
    df = pd.DataFrame(data)
    output_file = "data/collection.csv"
    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"✅ Export CSV terminé : {output_file}")


# Export Excel
def export_excel(collection: Collection):
    data = list(collection.find())
    df = pd.DataFrame(data)
    output_file = "data/collection.xlsx"
    df.to_excel(output_file, index=False)
    print(f"✅ Export Excel terminé : {output_file}")
