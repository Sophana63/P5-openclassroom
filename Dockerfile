FROM python:3.11

WORKDIR /app

# Installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie tout le reste
COPY . .

# Crée le dossier logs s'il n'existe pas
RUN mkdir -p logs

# Lance le script de migration
CMD ["python", "-m", "main"]