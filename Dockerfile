FROM python:3.11-slim

WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port 8000
EXPOSE 8000

# Commande par défaut
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 