# ============================================================
# wsgi.py — Point d'entrée WSGI pour la production
# ============================================================
# Gunicorn (le serveur de production) a besoin d'un objet
# d'application WSGI. Ce fichier crée cet objet en appelant
# la factory function create_app() définie dans app.py.
#
# En développement : python app.py
# En production    : gunicorn wsgi:app
# ============================================================

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
