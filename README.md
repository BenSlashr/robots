# Robots.txt Checker

Un outil complet pour vérifier et analyser les fichiers robots.txt selon les règles exactes de Googlebot.

## 🚀 Fonctionnalités

- **Analyse complète** : Vérifie le robots.txt selon les spécifications de Google
- **Interface moderne** : Design responsive avec Tailwind CSS
- **Tests de chemins** : Testez l'accessibilité de vos URLs
- **Multi User-Agents** : Support de tous les bots Google (Googlebot, Googlebot-Image, etc.)
- **Avertissements** : Détection des erreurs et bonnes pratiques
- **API REST** : Backend FastAPI avec documentation automatique

## 📋 Spécifications techniques

### Comportement Googlebot reproduit

- ✅ Limite de 500 KiB analysés
- ✅ Encodage UTF-8 avec caractères invalides remplacés
- ✅ Gestion des commentaires (#)
- ✅ Regroupement des directives par User-agent
- ✅ Sélection du groupe le plus spécifique
- ✅ Correspondance insensible au protocole/hôte
- ✅ Motifs avec * et ancrage $
- ✅ Règle la plus longue gagne, Allow prioritaire
- ✅ Gestion des redirections (max 5)
- ✅ Directives ignorées détectées

## 🛠️ Installation

### Prérequis

- Python 3.8+
- pip

### Installation des dépendances

```bash
pip install -r requirements.txt
```

## 🎯 Utilisation

### 1. Démarrer le serveur

```bash
python start.py
```

Le serveur démarrera sur `http://localhost:8000`

### 2. Utiliser l'interface web

Ouvrez le fichier `index.html` dans votre navigateur ou servez-le avec un serveur web local :

```bash
# Option 1: Serveur Python simple
python -m http.server 3000

# Option 2: Serveur Node.js (si installé)
npx serve .
```

### 3. API REST

L'API est disponible sur `http://localhost:8000/analyze`

Documentation interactive : `http://localhost:8000/docs`

#### Exemple d'appel API

```json
POST /analyze
{
  "url": "https://example.com",
  "user_agents": ["googlebot", "googlebot-image"],
  "test_paths": ["/", "/admin/", "/shop/"]
}
```

#### Réponse

```json
{
  "status": {
    "code": 200,
    "message": "OK",
    "size": 1234
  },
  "groups": [
    {
      "user_agent": "*",
      "allow_rules": ["/"],
      "disallow_rules": ["/admin/"],
      "sitemaps": ["https://example.com/sitemap.xml"]
    }
  ],
  "test_results": [
    {
      "path": "/",
      "user_agent": "googlebot",
      "allowed": true,
      "matched_rule": "Allow: /"
    }
  ],
  "warnings": []
}
```

## 🔧 Structure du projet

```
robots-txt/
├── index.html          # Interface web
├── app.js             # JavaScript front-end
├── main.py            # API FastAPI
├── start.py           # Script de démarrage
├── requirements.txt   # Dépendances Python
└── README.md         # Documentation
```

## 🎨 Interface utilisateur

L'interface propose :

- **Saisie URL** : Auto-complétion avec /robots.txt
- **Contenu direct** : Coller le robots.txt directement
- **Multi-sélection** : Choisir plusieurs User-Agents
- **Tests de chemins** : Tester plusieurs URLs
- **Résultats détaillés** : Tableaux responsive avec statut, groupes et tests

## 🐛 Gestion des erreurs

- **404/5xx** : Tout autorisé (comportement Google)
- **Timeout** : Gestion des timeouts réseau
- **Fichier trop gros** : Troncature à 500 KiB
- **Format invalide** : Avertissements détaillés

## 🚀 Déploiement

### Développement

```bash
python start.py
```

### Production

```bash
# Avec Gunicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Avec Docker
docker build -t robots-txt-checker .
docker run -p 8000:8000 robots-txt-checker
```

## 📖 Documentation API

La documentation complète de l'API est disponible automatiquement sur :
- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commit vos changements
4. Push vers la branche
5. Ouvrir une Pull Request

## 📝 Licence

Ce projet est sous licence MIT.

## 👨‍💻 Auteur

Développé par [Slashr](https://agence-slashr.fr) - Agence SEO à Lille 