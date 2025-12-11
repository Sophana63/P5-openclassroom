from src.migration import *
from src.crud import *
from src.export import *

# ===================== EXÉCUTION =====================
print("="*60)
print("DÉMARRAGE DE main.py")
print("="*60)

success = migrate()
if success:    
    print("\nSuccès de la migration !")
else:
    print("\nMigration échouée. Voir migration_report.log")

patient = {
    "Name": "John Doe",
    "Age": "45",
    "Gender": "Male",
    "Blood Type": "O+",
    "Medical Condition": "Diabetes",
    "Date of Admission": "2024-01-15",
    "Doctor": "Dr. Smith",
    "Hospital": "General Hospital",
    "Insurance Provider": "Mutuelle X",
    "Billing Amount": "1234.5666666",
    "Room Number": "101",
    "Admission Type": "Emergency",
    "Discharge Date": "2024-01-20",
    "Medication": "Insulin",
    "Test Results": "Stable"
}

print(add_patient(patient))

last_patient = collection.find().sort("_id", -1).limit(1).__next__()
id_patient = last_patient["patient_id"]

print("\n--- Lecture du dernier patient enregistré---")
read_patient(id_patient)

print("\n--- Mise à jour ---")
updates = {
    "Age": 46,
    "Medical Condition": "Diabète de type 2 stabilisé",
    "Test Results": "Normal"
}
print(update_patient(id_patient, updates))

print("\n--- Lecture après mise à jour---")
read_patient(id_patient)

print("\n--- Suppression du patient ---")
print(delete_patient(id_patient))

print("\n--- Test de recherche par nom du patient 'jackson' ---")
read_patient("jackson")

print("\n--- Exportation de la BDD au format CSV, JSON et Excel ---")
export_json(collection)
export_csv(collection)
export_excel(collection)