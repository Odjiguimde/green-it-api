# 🌿 Green IT API — Surveillance Environnementale

API RESTful Flask connectée à MongoDB Atlas pour la surveillance de la qualité de l'air au Sénégal.

**Projet NoSQL — INGC 2 InDIA 2026 — ESMT Dakar**

---

## 🛠️ Technologies

- **Python 3.11+** + **Flask 3.1**
- **MongoDB Atlas** (base de données NoSQL cloud)
- **PyMongo 4.10** (driver MongoDB)
- **Gunicorn** (serveur WSGI production)

---

## 🚀 Installation locale

```bash
# 1. Cloner le dépôt
git clone https://github.com/<username>/green-it-api.git
cd green-it-api

# 2. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et renseigner votre URI MongoDB Atlas

# 5. Lancer l'API
python app.py
```

L'API sera accessible sur `http://127.0.0.1:5000`

---

## ⚙️ Variables d'environnement

| Variable | Description | Exemple |
|----------|-------------|---------|
| `MONGO_URI` | URI de connexion MongoDB Atlas | `mongodb+srv://user:pass@cluster.mongodb.net/` |
| `DB_NAME` | Nom de la base de données | `green_it_db` |
| `FLASK_DEBUG` | Mode debug | `True` / `False` |

---

## 📡 Endpoints principaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Health check |
| GET | `/api/stations/` | Liste des stations |
| GET | `/api/stations/<id>` | Station par ID |
| GET | `/api/stations/filter/aqi?min_aqi=100` | Filtre par AQI |
| POST | `/api/stations/` | Créer une station |
| PATCH | `/api/stations/<id>` | Modifier une station |
| DELETE | `/api/stations/<id>` | Supprimer une station |
| GET | `/api/analytics/nearby?lng=X&lat=Y` | Stations proches (géospatial) |
| GET | `/api/analytics/city-stats?days=30` | Stats par ville (agrégation) |
| POST | `/api/analytics/seed` | Insérer données de test |

---

## 🗄️ Index MongoDB requis

```js
db.stations.createIndex({ "location": "2dsphere" })
```

---

## 📄 Licence

Projet académique — ESMT Dakar 2026
