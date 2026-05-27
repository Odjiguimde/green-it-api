# ============================================================
# app.py — Point d'entrée principal de l'API Flask
# ============================================================
# Ce fichier est le cœur de l'application. Il crée l'instance
# Flask, enregistre les Blueprints (modules de routes) et
# configure les gestionnaires d'erreurs globaux.
#
# Architecture :
#   app.py              ← Ce fichier (orchestrateur)
#   ├── config.py       ← Connexion MongoDB Atlas
#   └── routes/
#       ├── stations.py ← Routes CRUD (R1, R2, R3)
#       └── analytics.py← Routes avancées (R4, R5)
# ============================================================

import os
from flask import Flask, jsonify
from dotenv import load_dotenv

# Chargement des variables d'environnement depuis .env
# Doit être fait AVANT l'import des modules qui en dépendent
load_dotenv()

# Import des Blueprints (modules de routes)
from routes.stations import stations_bp
from routes.analytics import analytics_bp


def create_app():
    """
    Factory function qui crée et configure l'application Flask.

    L'utilisation d'une factory function (plutôt qu'une instance globale)
    est une bonne pratique qui facilite les tests unitaires et le déploiement
    multi-environnement.

    Returns:
        Flask: L'application Flask configurée et prête à démarrer.
    """

    app = Flask(__name__)

    # ── Enregistrement des Blueprints ─────────────────────────────────────
    # Chaque Blueprint apporte ses routes préfixées à l'application principale.
    # /api/stations/* → géré par stations_bp
    # /api/analytics/* → géré par analytics_bp
    app.register_blueprint(stations_bp)
    app.register_blueprint(analytics_bp)

    # ── Route racine : Health Check ───────────────────────────────────────
    @app.route("/", methods=["GET"])
    def health_check():
        """
        Endpoint de vérification que l'API est bien en ligne.
        Utile pour les outils de monitoring et les déploiements.
        """
        return jsonify({
            "status": "online",
            "message": "Green IT API — Stations de Mesure Environnementale",
            "version": "1.0.0",
            "endpoints": {
                "stations": "/api/stations/",
                "analytics": "/api/analytics/"
            }
        }), 200

    # ── Gestionnaires d'erreurs globaux ───────────────────────────────────
    # Ces handlers interceptent les erreurs HTTP et retournent
    # une réponse JSON cohérente plutôt qu'une page HTML d'erreur.

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "status": "error",
            "code": 404,
            "message": "La ressource demandée est introuvable."
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "status": "error",
            "code": 405,
            "message": "Méthode HTTP non autorisée pour cet endpoint."
        }), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "status": "error",
            "code": 500,
            "message": "Erreur interne du serveur."
        }), 500

    return app


# ── Lancement du serveur ──────────────────────────────────────────────────────
# Ce bloc n'est exécuté que si on lance directement ce fichier
# (python app.py), pas lors d'un import par un autre module.

if __name__ == "__main__":
    flask_app = create_app()

    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    print(f"\n{'='*55}")
    print(f"  🌿 Green IT API — Démarrage du serveur Flask")
    print(f"  📡 URL locale : http://127.0.0.1:{port}/")
    print(f"  🔧 Mode debug : {'Activé' if debug else 'Désactivé'}")
    print(f"{'='*55}\n")

    flask_app.run(host="0.0.0.0", port=port, debug=debug)
