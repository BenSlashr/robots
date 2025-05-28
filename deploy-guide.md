# Guide de Déploiement Docker - Robots.txt Checker

## 🐳 Déploiement avec Docker

### Prérequis
- Docker installé
- Docker Compose installé (optionnel mais recommandé)

### Méthode 1 : Docker Compose (Recommandée)

```bash
# Cloner ou télécharger le projet
git clone <votre-repo>
cd robots-txt

# Construire et lancer le conteneur
docker-compose up --build

# En mode détaché (arrière-plan)
docker-compose up --build -d

# Arrêter le service
docker-compose down
```

### Méthode 2 : Docker directement

```bash
# Construire l'image
docker build -t robots-checker .

# Lancer le conteneur
docker run -p 8000:8000 robots-checker

# En mode détaché
docker run -d -p 8000:8000 --name robots-checker robots-checker

# Arrêter le conteneur
docker stop robots-checker
docker rm robots-checker
```

## 🌐 Accès à l'application

Une fois déployée, l'application sera accessible sur :
- **Interface web** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **API endpoint** : http://localhost:8000/analyze

## 🔧 Spécificités techniques

### Architecture
- **Backend** : FastAPI servant l'API ET les fichiers statiques
- **Frontend** : HTML/CSS/JS statique servi par FastAPI
- **Port** : 8000 (mappé sur l'hôte)

### Avantages de cette approche
✅ **Une seule image Docker** pour frontend + backend
✅ **Pas de problèmes CORS** (même origine)
✅ **URLs relatives** qui fonctionnent en prod
✅ **Configuration simplifiée**

### Modifications apportées
1. **FastAPI serve les fichiers statiques** via `StaticFiles`
2. **Route `/` retourne `index.html`** directement
3. **API_BASE_URL** devient `window.location.origin`
4. **Docker optimisé** avec .dockerignore

## 🚀 Déploiement en production

### Variables d'environnement
```bash
# Production
docker run -d \
  -p 80:8000 \
  -e PYTHONUNBUFFERED=1 \
  --name robots-checker-prod \
  robots-checker
```

### Avec reverse proxy (nginx)
```nginx
server {
    listen 80;
    server_name votre-domaine.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Avec domaine personnalisé
L'application s'adapte automatiquement grâce à `window.location.origin` :
- Local : `http://localhost:8000`
- Production : `https://votre-domaine.com`

## 📝 Logs et Debugging

```bash
# Voir les logs en temps réel
docker-compose logs -f

# Logs d'un conteneur spécifique
docker logs robots-checker

# Shell dans le conteneur
docker exec -it robots-checker /bin/bash
```

## 🔄 Mise à jour

```bash
# Reconstruire après modifications
docker-compose down
docker-compose up --build

# Ou forcer la reconstruction
docker-compose build --no-cache
docker-compose up
``` 