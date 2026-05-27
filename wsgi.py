# ============================================================
# wsgi.py — Point d'entrée WSGI pour la production Render
# ============================================================

import os
import sys

# Ajoute le répertoire courant au chemin de recherche de Python
# Cela garantit que 'routes', 'db' et 'config' soient toujours trouvés par Render
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

# Gunicorn va chercher la variable globale nommée 'app'
app = create_app()

if __name__ == "__main__":
    app.run()
