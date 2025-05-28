#!/usr/bin/env python3
"""
Script de démarrage pour le Robots.txt Checker
"""

import uvicorn

if __name__ == "__main__":
    print("🚀 Démarrage du Robots.txt Checker")
    print("📖 Documentation API: http://localhost:8000/docs")
    print("🌐 Interface web: ouvrez index.html dans votre navigateur")
    print("⚡ API endpoint: http://localhost:8000/analyze")
    print()
    
    uvicorn.run(
        "main:app",  # Utiliser une string d'import au lieu de l'objet
        host="0.0.0.0",
        port=8000,
        reload=True,  # Rechargement automatique en développement
        log_level="info"
    ) 