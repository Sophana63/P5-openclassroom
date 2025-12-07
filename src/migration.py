import os
import logging
from datetime import datetime
import pandas as pd
from tabulate import tabulate

# Pour une connexion sécurisée
from .connection import MongoDBConnection

# ===================== CONFIGURATION =====================
CSV_PATH = "./data/healthcare_dataset.csv"
BATCH_SIZE = 1000

# Configuration du logging
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "migration_report.log")

logging.basicConfig(
    filename=log_file,
    encoding='utf-8',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a',
    force=True
)

# ===================== CONNEXION SÉCURISÉE =====================
print("Connexion à MongoDB en cours...")
mongo = MongoDBConnection()

if not mongo.connect():
    print("Échec de la connexion. Arrêt du script.")
    exit(1)

collection = mongo.collection
print(f"Connecté à la base '{mongo.db_name}' → collection '{mongo.collection_name}'")

# ===================== FONCTIONS =====================
def check_data_integrity(df: pd.DataFrame):
    """Vérifications complètes avant migration"""
    print("\nVérification de l'intégrité des données...")
    logging.info("Début vérification intégrité données")

    issues = []
    print(f"→ {len(df):,} lignes | {len(df.columns)} colonnes")

    # Valeurs manquantes
    missing = df.isnull().sum()
    if missing.sum() > 0:
        print("Valeurs manquantes détectées :")
        print(missing[missing > 0])

    # Doublons sur patient_id
    if 'patient_id' in df.columns:
        dup = df['patient_id'].duplicated().sum()
        if dup > 0:
            issues.append(f"{dup} doublons sur patient_id")
            logging.warning(f"{dup} doublons détectés sur patient_id")

    # Typage
    if 'diagnosis_date' in df.columns:
        df['diagnosis_date'] = pd.to_datetime(df['diagnosis_date'], errors='coerce')

    if issues:
        print("Attention : Problèmes détectés :", issues)
    else:
        print("Données propres et prêtes pour la migration")
    logging.info("Vérification intégrité terminée")
    return df

def generate_patient_id(row_index: int) -> str:
    """Génère P00001, P00002, P00003..."""
    return f"P{row_index + 1:05d}"   # :05d → 5 chiffres avec zéros

# ===================== SUPPRESSION DE L'ANCIENNE COLLECTION =====================
print("==========================================")
print(f"Suppression de l'ancienne collection ''{mongo.collection_name}' si elle existe...")
collection.drop()                                     
print(f"Collection '{mongo.collection_name} supprimée (ou inexistante → OK)")
logging.info("Ancienne collection supprimée avant nouvelle migration")
print("==========================================")

def migrate():
    """Migration principale"""
    start = datetime.now()
    logging.info("=== DÉBUT DE LA MIGRATION ===")
    print("\nDémarrage de la migration...")

    if not os.path.exists(CSV_PATH):
        print(f"Fichier introuvable : {CSV_PATH}")
        return False

    df = pd.read_csv(CSV_PATH)
    df = check_data_integrity(df)
    
    df['patient_id'] = [generate_patient_id(i) for i in range(len(df))]

    # patient_id en première colonne 
    cols = ['patient_id'] + [col for col in df.columns if col != 'patient_id']
    df = df[cols]

    records = df.to_dict("records")
    total = len(records)
    print(f"\nInsertion de {total:,} patients par batchs de {BATCH_SIZE}...")

    for i in range(0, total, BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        try:
            collection.insert_many(batch, ordered=False)
        except Exception as e:
            logging.warning(f"Erreurs ignorées dans le batch {i//BATCH_SIZE + 1}: {e}")

        print(f"Progression : {min(i + BATCH_SIZE, total):,}/{total:,}")    

    duration = datetime.now() - start
    count = collection.count_documents({})
    print(f"\nMIGRATION TERMINÉE EN {duration} !")
    print(f"→ {count:,} patients insérés dans MongoDB")
    logging.info(f"Migration réussie - {count} documents - durée {duration}")
    logging.info(f"Date : {start} ")
    logging.info(f"==========================================")

    return True

# ===================== EXÉCUTION =====================

success = migrate()
if success:    
    print("\nSuccès de la migration !")
else:
    print("\nMigration échouée. Voir migration_report.log")