# Medical Data Migration – Étape 1 : MongoDB local sécurisé

Projet réalisé dans le cadre de mon stage Data Engineer chez **DataSoluTech**  
Objectif : installer MongoDB en local de façon propre, sécurisée et reproductible avec Docker, puis mettre en place un système d’authentification complet avec rôles dédiés.

## Prérequis 

### 1. Visual Studio Code
- Téléchargement : https://code.visualstudio.com/
- Extensions utiles installées :
  - Python

### 2. Docker Desktop
- Téléchargement : https://www.docker.com/products/docker-desktop/
- Version installée : Docker Desktop 4.52.0
- Installation du noyau WSL : ``wsl –install`` via PowerShell
- Ou mise à jour du noyau WSL : ``wsl –update`` via PowerShell

### 3. Installation de MongoDB (Docker)
- Récupération de l’image officielle : ``docker pull mongo:latest``
- Version installée : 7.0.14

## Projet 

### 1. Création du fichier docker-compose.yml

 - permet de décrire et lancer plusieurs services Docker ensemble.

<details>
  <summary>Cliquer pour afficher</summary>

  ```YAML
# docker-compose.yml – Configuration MongoDB locale sécurisée et reproductible
# Projet : Migration données médicales – DataSoluTech – Nov. 2025
version: '3.9'                            # Version du format docker-compose

services:
  mongo:                                  # Nom du service
    image: mongo:7.0.14                   # Image officielle MongoDB – version figée 7.0.14 (reproductibilité garantie)
                                          
    container_name: mongodb-medical       # Nom fixe du conteneur

    restart: unless-stopped               # Politique de redémarrage : redémarre automatiquement si crash ou reboot PC
                                          # sauf si tu fais explicitement "docker stop"

    environment:                          # Variables d’environnement lues par MongoDB au démarrage
      MONGO_INITDB_ROOT_USERNAME: admin   # → Crée automatiquement un super-utilisateur
      MONGO_INITDB_ROOT_PASSWORD: admin1234
      MONGO_INITDB_DATABASE: medical_db   # → Crée automatiquement la base "medical_db"

    ports:
      - "27017:27017"                     # Exposition du port MongoDB
                                          # format : "port_hôte:port_conteneur"
                                          # → connexion sur localhost:27017 depuis le PC

    volumes:
      - mongo-data:/data/db               # Volume nommé → persistance des données même si tu supprimes le conteneur
                                          # toutes tes données médicales restent sauvegardées

      - ./init-db:/docker-entrypoint-initdb.d   # POINT MAGIQUE
                                          # → Tout fichier .js placé dans le dossier local ./init-db
                                          #    sera exécuté AUTOMATIQUEMENT au PREMIER démarrage
                                          #    (création users/rôles sans aucune commande manuelle)

    command: --auth                       # Force l’authentification OBLIGATOIRE
                                          # sans ça, n’importe qui pourrait se connecter sans mot de passe

# ------------------------------------------------------------------
# Section volumes : déclaration des volumes nommés utilisés ci-dessus
# ------------------------------------------------------------------
volumes:
  mongo-data:                             # Volume persistant pour /data/db
                                          # Suppression possible avec "docker compose down -v" (reset complet)
```
</details>

### 2. Création des utilisateurs

- fichier : init-db/create-users.js
- création automatique des utilisateurs au premier lancement

<details>
  <summary>Cliquer pour afficher</summary>

```javascript
// init-db/create-users.js 
print("Création des utilisateurs et rôles dédiés pour le projet médical");

db = db.getSiblingDB('medical_db');

// 1. Admin base
db.createUser({
  user: "admin-db",
  pwd: "Admin2025!",
  roles: [
    { role: "readWrite", db: "medical_db" },
    { role: "dbAdmin", db: "medical_db" },
    { role: "userAdmin", db: "medical_db" }
  ]
});

// 2. Application métier
db.createUser({
  user: "app-user",
  pwd: "AppMedical42",
  roles: [
    { role: "readWrite", db: "medical_db" }
  ]
});

// 3. Lecture seule
db.createUser({
  user: "read-only",
  pwd: "ReadOnly2025",
  roles: [
    { role: "read", db: "medical_db" }
  ]
});

print("Tous les 3 utilisateurs ont été créés avec succès !");
```  
</details>  

<br>
<b>Résumé des utilisateurs créés</b>  

| Utilisateur   | Mot de passe     | Rôles principaux                     | Usage prévu              |
|----------------|------------------|--------------------------------------|--------------------------|
| admin         | admin1234        | `root`                               | Admin serveur            |
| admin-db      | Admin2025!       | `readWrite`, `dbAdmin`, `userAdmin`  | Admin de la base médicale|
| app-user      | AppMedical42     | `readWrite`                          | Application métier       |
| read-only     | ReadOnly2025     | `read`                               | Audit / reporting        |


### 3. Lancement du projet

```bash
docker compose up -d
```
- ``up`` : démarre tous les services définis.
- ``-d`` : permet au terminal de rendre la main immédiatement.

<br>
Connexion & vérification

```bash
# connexion au shell MongoDB (mongosh) avec l’utilisateur root admin
docker exec -it mongodb-medical mongosh -u admin -p admin1234
```

```javascript
use medical_db      // pointe sur la bdd medical_db
db.getUsers()       // vérifie si tous les utilisateurs ont été créés
```

### 4. Migration des données avec python

Pipeline complet de migration du dataset médical (`healthcare_dataset.csv`) vers MongoDB, réalisé en Python.

<b>Structure du projet</b>

```txt
medical-migration/
├── data/
│   └── healthcare_dataset.csv          # Dataset source (55 500 patients)
├── logs/
│   └── migration_report.log            # Log détaillé de chaque exécution (UTF-8, accents OK)
├── src/
│   └── migration.py                    # Script principal de migration
│   └── connection.py                   # Classe pour se connecter à MongoDB
├── .env                                # Variables d'environnement (NE JAMAIS commiter !)
├── .gitignore
├── requirements.txt
└── README.md
```

<b>Fichiers clés:</b>
- ``requirements.txt`` : installe les dépendances (pymongo, pandas...)
  - commande : `pip install -r requirements.txt`
- ``.env`` : stocke les variables d'environnement (ici, pour se connecter la base de données)
- ``.gitignore`` : indique à Git les fichiers ou les répertoires à ignorer (comme le .env par exemple)

<br>
<b>Fichiers python:</b>

- ``connection.py`` : 
  - Dédié à la création et à la gestion de la connexion à MongoDB
  - Charge les variables d’environnement depuis le `.env`
  - Crée un client MongoDB sécurisé (`MongoClient`) avec utilisateur/mot de passe
  - Retourne la collection `patients`
- ``migration.py`` :
  - Lecture du fichier CSV et le transforme en dataFrame
  - Nettoyage automatique de la collection avant migration (`drop` contrôlé par variable)
  - Génération d’identifiant métier lisible : `patient_id` → `P00001`, `P00002`, …, `P55500`
  - Logs complets et lisibles : Fichier `logs/migration_report.log` en **UTF-8** (pour les accents : é, è, ç, à…)

  ### AWS

  Tarification Sans Serveur

  Tarification Instances à la demande provisionnée
