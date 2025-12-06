import os
from pymongo import MongoClient
import logging
from dotenv import load_dotenv

# Charge les variables d'environnement depuis un fichier .env
load_dotenv()

class MongoDBConnection:
    def __init__(self):
        self.host = os.getenv("MONGO_HOST")
        self.port = int(os.getenv("MONGO_PORT"))
        self.username = os.getenv("MONGO_USER")
        self.password = os.getenv("MONGO_PASSWORD")
        self.auth_source = os.getenv("MONGO_AUTH_SOURCE")
        self.db_name = os.getenv("MONGO_DB")
        self.collection_name = os.getenv("MONGO_COLLECTION")

        # Vérification immédiate que tout est bien chargé
        missing = [var for var, val in vars(self).items() if val is None]
        if missing:
            raise ValueError(f"Variables manquantes dans .env : {missing}")
        
        self.client = None
        self.db = None
        self.collection = None

    def connect(self):
        try:
            self.client = MongoClient(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                authSource=self.auth_source,
                authMechanism="SCRAM-SHA-256"
            )
            self.client.admin.command('ping')
            print("Connexion MongoDB réussie")
            logging.info("Connexion MongoDB établie")

            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            return True

        except Exception as e:
            print(f"Échec connexion MongoDB → {e}")
            logging.error(f"Connexion échouée : {e}")
            return False