# ============================================================
# config.py — Configuration de la connexion MongoDB Atlas
# ============================================================
# Ce module centralise toute la logique de connexion à la base
# de données. En isolant cette configuration ici, on respecte
# le principe de séparation des responsabilités (SoC) et on
# facilite les changements d'environnement (dev/prod).
# ============================================================

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Charger les variables définies dans le fichier .env
load_dotenv()


def get_db():
    """
    Établit et retourne une connexion à la base de données MongoDB Atlas.

    Returns:
        pymongo.database.Database: L'objet base de données prêt à l'emploi.

    Raises:
        ConnectionFailure: Si la connexion à MongoDB Atlas échoue.
        ValueError: Si la variable MONGO_URI n'est pas définie dans .env.
    """

    # Récupération sécurisée de l'URI depuis les variables d'environnement
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME", "green_it_db")  # Valeur par défaut si absent

    if not mongo_uri:
        raise ValueError(
            "MONGO_URI est introuvable. "
            "Vérifiez votre fichier .env."
        )

    try:
        # Création du client MongoDB avec un timeout de connexion de 5 secondes
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

        # Vérification que la connexion est bien établie (ping le serveur)
        client.admin.command("ping")
        print(f"[✓] Connexion à MongoDB Atlas réussie — Base : '{db_name}'")

        return client[db_name]

    except Exception as e:
        # ICI : On affiche l'erreur réelle dans les logs de Render pour comprendre le problème !
        print(f"[✗] ERREUR CRUCIALE MONGODB : {str(e)}")
        raise e
