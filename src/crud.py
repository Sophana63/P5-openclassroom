from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime
import logging, os
from dotenv import load_dotenv
from connection import MongoDBConnection


# ===================== INITIALISATION DE LA CONNEXION =====================
print("Initialisation de connexion à MongoDB...")
mongo = MongoDBConnection()

if not mongo.connect():
    print("Impossible de se connecter à MongoDB. Arrêt du script.")
    exit(1)

collection = mongo.collection
print(f"Connecté → {mongo.db_name}.{mongo.collection_name}")

# On s'assure qu'il y a un index unique sur patient_id
try:
    collection.create_index("patient_id", unique=True)
    print("Index unique sur 'patient_id' vérifié/créé")
except Exception as e:
    print("Index déjà existant ou erreur mineure :", e)


# ===================== VALIDATION & TYPAGE =====================
from datetime import datetime

ALLOWED_GENDERS = {"Male", "Female", "Other"}
ALLOWED_BLOOD_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}

def validate_date(value: str) -> datetime | bool:
    if not value:
        return False
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d")
    except ValueError:
        return False

def validate_patient(patient_data: dict) -> dict | bool:
    """
    Retourne un dictionnaire nettoyé si tout est valide, sinon False.
    """

    required_fields = [
        "Name", "Age", "Gender", "Blood Type", "Medical Condition",
        "Date of Admission", "Doctor", "Hospital", "Insurance Provider",
        "Billing Amount", "Room Number", "Admission Type",
        "Discharge Date", "Medication", "Test Results"
    ]

    # Vérifier la présence de toutes les clés
    for field in required_fields:
        if field not in patient_data:
            print(f"Champ manquant : {field}")
            return False

    validated = {}

    # Name
    if isinstance(patient_data["Name"], str) and patient_data["Name"].strip():
        validated["Name"] = patient_data["Name"].strip()
    else:
        return False

    # Age
    try:
        age = int(patient_data["Age"])
        if not (0 <= age <= 150):
            return False
        validated["Age"] = age
    except:
        return False

    # Gender
    gender = patient_data["Gender"].strip()
    if gender not in ALLOWED_GENDERS:
        return False
    validated["Gender"] = gender

    # Blood Type
    blood = patient_data["Blood Type"].strip()
    if blood not in ALLOWED_BLOOD_TYPES:
        return False
    validated["Blood Type"] = blood

    # Medical Condition
    validated["Medical Condition"] = patient_data["Medical Condition"].strip()

    # Dates
    date_adm = validate_date(patient_data["Date of Admission"])
    date_discharge = validate_date(patient_data["Discharge Date"])

    if not date_adm or not date_discharge:
        return False

    validated["Date of Admission"] = date_adm
    validated["Discharge Date"] = date_discharge

    # Doctor, Hospital, Insurance Provider, Admission Type
    for key in ["Doctor", "Hospital", "Insurance Provider", "Admission Type"]:
        if isinstance(patient_data[key], str) and patient_data[key].strip():
            validated[key] = patient_data[key].strip()
        else:
            return False

    # Billing Amount
    try:
        amount = float(patient_data["Billing Amount"])
        validated["Billing Amount"] = amount
    except:
        return False

    # Room Number
    try:
        validated["Room Number"] = int(patient_data["Room Number"])
    except:
        return False

    # Medication / Test Results
    validated["Medication"] = patient_data["Medication"]
    validated["Test Results"] = patient_data["Test Results"]

    return validated



# ===================== FONCTIONS CRUD =====================
def get_next_patient_id() -> str:
    """
    Retourne le prochain patient_id disponible au format P00001, P00002, ...
    """
    last_doc = collection.find_one(sort=[("patient_id", -1)])
    
    try:
        last_id = last_doc["patient_id"]  # ex: "P054321"
        number = int(last_id[1:])         # → 54321
    except (TypeError, KeyError, ValueError):
        number = 0

    next_number = number + 1
    return f"P{next_number:05d}"


def add_patient(patient_data: dict) -> str:
    """
    Ajoute un patient si patient_id n'existe pas déjà.
    Si pas de patient_id fourni → en génère un automatiquement.
    Retourne le patient_id final utilisé.
    """
    
    print(collection)
    # Valider la structure et les champs
    validated = validate_patient(patient_data)
    if not validated:
        return "❌ Données invalides — patient non ajouté."
    # Si pas de patient_id fourni → on en génère un
    collection.create_index("patient_id", unique=True)
    if "patient_id" not in validated or not validated["patient_id"]:
        validated["patient_id"] = get_next_patient_id()
    
    # Vérifie s'il existe déjà (au cas où)
    try:
        result = collection.insert_one(validated)
        return f"✔️ Patient ajouté avec _id {validated['patient_id']}"
    except DuplicateKeyError:
        return "❌ Patient non ajouté — patient_id déjà existant. Réessayez."



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

from export import *

export_json(collection)
export_csv(collection)
export_excel(collection)