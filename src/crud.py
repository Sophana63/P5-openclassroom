from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime
import logging, os
from dotenv import load_dotenv
from .connection import MongoDBConnection


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
        return f"✔️ Patient {validated['Name']} ajouté avec l'id {validated['patient_id']}"
    except DuplicateKeyError:
        return "❌ Patient non ajouté — patient_id déjà existant. Réessayez."
    
def read_patient(search: str) -> list[dict]:
    """
    Recherche des patients par patient_id OU par nom (insensible à la casse, recherche partielle).
    Retourne une liste de patients trouvés (peut être vide, 1 ou plusieurs).
    """
    if not search or not isinstance(search, str):
        print("❌ Terme de recherche invalide.")
        return []

    search = search.strip()
    patients = []

    # 1. Recherche exacte par patient_id 
    if search.upper().startswith("P") and search[1:].isdigit():
        patient = collection.find_one({"patient_id": search.upper()})
        if patient:
            patients = [patient]
            print(f"✔️ Patient trouvé par ID : {search.upper()}")
        else:
            print(f"❌ Aucun patient trouvé avec l'ID : {search.upper()}")

    # 2. Si pas trouvé par ID → recherche par nom 
    if not patients:
        # Recherche partielle avec expression régulière
        regex_query = {"$regex": search, "$options": "i"}  # i => insensible à la casse
        cursor = collection.find({"Name": regex_query}).limit(20)  # limite la recherche à 20 résultats

        patients = list(cursor)

        if patients:
            print(f"✔️ {len(patients)} patient(s) trouvé(s) contenant '{search}' dans le nom :")
        else:
            print(f"❌ Aucun patient trouvé avec le nom contenant '{search}'.")

    # Affichage des résultats
    for patient in patients:
        print(f"   → {patient['patient_id']} | {patient.get('Name', 'Inconnu')} | {patient.get('Age', '?')} ans | {patient.get('Medical Condition', 'Inconnue')}")
        adm_date = patient.get("Date of Admission")
        if isinstance(adm_date, datetime):
            adm_date = adm_date.strftime("%d/%m/%Y")
        print(f"     Admission : {adm_date} | Hôpital : {patient.get('Hospital', 'Inconnu')}")
        print("   " + "-"*50)

    return patients

def update_patient(patient_id: str, updates: dict) -> str:
    """
    Met à jour un patient existant.
    updates : dictionnaire avec seulement les champs à modifier.
    Retourne un message de succès ou d'erreur.
    """
    if not patient_id or not isinstance(patient_id, str):
        return "❌ patient_id invalide."

    patient_id = patient_id.strip().upper()

    # Vérifier que le patient existe
    if not collection.find_one({"patient_id": patient_id}):
        return f"❌ Patient {patient_id} non trouvé — mise à jour impossible."

    # Valider les champs fournis (on réutilise la même logique que validate_patient)
    validated_updates = {}
    for key, value in updates.items():
        if key == "Age":
            try:
                age = int(value)
                if 0 <= age <= 150:
                    validated_updates["Age"] = age
                else:
                    return f"❌ Âge invalide ({value})."
            except:
                return f"❌ Âge doit être un nombre entier."

        elif key == "Gender":
            gender = str(value).strip()
            if gender in ALLOWED_GENDERS:
                validated_updates["Gender"] = gender
            else:
                return f"❌ Genre invalide (doit être Male, Female ou Other)."

        elif key == "Blood Type":
            blood = str(value).strip()
            if blood in ALLOWED_BLOOD_TYPES:
                validated_updates["Blood Type"] = blood
            else:
                return f"❌ Groupe sanguin invalide."

        elif key in ["Name", "Doctor", "Hospital", "Insurance Provider", "Admission Type", "Medication", "Test Results", "Medical Condition"]:
            if isinstance(value, str) and value.strip():
                validated_updates[key] = value.strip()
            else:
                return f"❌ {key} ne peut pas être vide."

        elif key == "Billing Amount":
            try:
                amount = float(str(value).replace(",", "."))
                validated_updates["Billing Amount"] = round(amount, 2)
            except:
                return f"❌ Montant invalide."

        elif key == "Room Number":
            try:
                validated_updates["Room Number"] = int(value)
            except:
                return f"❌ Numéro de chambre invalide."

        elif key in ["Date of Admission", "Discharge Date"]:
            date_obj = validate_date(value)
            if date_obj:
                validated_updates[key] = date_obj
            else:
                return f"❌ Format de date invalide pour {key} (YYYY-MM-DD requis)."

        else:
            return f"❌ Champ inconnu : {key}"

    # Appliquer la mise à jour
    try:
        result = collection.update_one(
            {"patient_id": patient_id},
            {"$set": validated_updates}
        )
        if result.modified_count:
            print(f"✔️ Patient {patient_id} mis à jour avec succès.")
            logging.info(f"Mise à jour patient : {patient_id} → {validated_updates}")
            return f"✔️ Mise à jour réussie pour {patient_id}"
        else:
            return "ℹ️ Aucune modification appliquée (valeurs identiques)."
    except Exception as e:
        return f"❌ Erreur lors de la mise à jour : {e}"
    
def delete_patient(patient_id: str) -> str:
    """
    Supprime un patient par patient_id.
    Demande confirmation si lancé interactivement.
    """
    if not patient_id or not isinstance(patient_id, str):
        return "❌ patient_id invalide."

    patient_id = patient_id.strip().upper()

    # Vérifier existence
    patient = collection.find_one({"patient_id": patient_id})
    if not patient:
        return f"❌ Patient {patient_id} non trouvé — rien à supprimer."

    # Confirmation (sauf si lancé en script automatisé)
    if os.isatty(0):  # si on est dans un terminal interactif
        confirm = input(f"⚠️  Confirmez la suppression de {patient_id} ({patient.get('Name', 'Inconnu')}) ? (oui/NON) : ")
        if confirm.lower() != "oui":
            return "❌ Suppression annulée."

    try:
        result = collection.delete_one({"patient_id": patient_id})
        print(f"🗑️ Patient {patient_id} supprimé définitivement.")
        logging.warning(f"Suppression patient : {patient_id} | {patient.get('Name')}")
        return f"✔️ Patient {patient_id} supprimé."
    except Exception as e:
        return f"❌ Erreur lors de la suppression : {e}"