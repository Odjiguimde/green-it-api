# ============================================================
# routes/stations.py — Routes CRUD des stations de mesure
# ============================================================
# Ce module gère les opérations de base (Create, Read, Update,
# Delete) sur la collection "stations" de MongoDB.
#
# Requêtes couvertes :
#   R1 — Lire une station par son ID (GET)
#   R2 — Filtrer les stations avec un AQI supérieur à un seuil (GET)
#   R3 — Créer une nouvelle station (POST)
#   R3b— Mettre à jour une mesure existante (PATCH)
#   R3c— Supprimer une station (DELETE)
#   R0 — Lister toutes les stations avec pagination (GET)
# ============================================================

from flask import Blueprint, request, jsonify
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from config import get_db

# --- Création du Blueprint ---
# Un Blueprint est un composant Flask qui regroupe des routes liées.
# Il sera enregistré dans app.py via app.register_blueprint().
stations_bp = Blueprint("stations", __name__, url_prefix="/api/stations")

# Connexion à la base de données et accès à la collection "stations"
db = get_db()
collection = db["stations"]


# ── Utilitaire ────────────────────────────────────────────────────────────────

def serialize_doc(doc):
    """
    Convertit un document MongoDB en dict JSON-sérialisable.
    L'ObjectId de MongoDB n'est pas directement sérialisable en JSON,
    il faut donc le convertir en chaîne de caractères.
    """
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ── R0 : Lister toutes les stations (avec pagination) ────────────────────────

@stations_bp.route("/", methods=["GET"])
def get_all_stations():
    """
    Retourne la liste de toutes les stations de mesure.

    Paramètres de requête (query params) :
        page  (int) : Numéro de page (défaut: 1)
        limit (int) : Nombre de résultats par page (défaut: 10, max: 100)

    Exemple : GET /api/stations/?page=1&limit=5
    """
    try:
        # Récupération et validation des paramètres de pagination
        page = max(1, int(request.args.get("page", 1)))
        limit = min(100, max(1, int(request.args.get("limit", 10))))
        skip = (page - 1) * limit

        # Requête MongoDB : find() retourne tous les documents
        # .skip() et .limit() assurent la pagination
        stations = list(collection.find().skip(skip).limit(limit))
        total = collection.count_documents({})

        return jsonify({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total,
            "data": [serialize_doc(s) for s in stations]
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ── R1 : Obtenir une station par son ID ───────────────────────────────────────

@stations_bp.route("/<station_id>", methods=["GET"])
def get_station_by_id(station_id):
    """
    Retourne les données complètes d'une station identifiée par son ObjectId MongoDB.

    Paramètre d'URL :
        station_id (str) : L'identifiant MongoDB de la station (_id)

    Exemple : GET /api/stations/665f1a2b3c4d5e6f7a8b9c0d
    """
    try:
        # Conversion de la chaîne en ObjectId MongoDB
        # Lève InvalidId si le format est incorrect (pas 24 caractères hex)
        obj_id = ObjectId(station_id)

    except InvalidId:
        return jsonify({
            "status": "error",
            "message": f"'{station_id}' n'est pas un ObjectId valide."
        }), 400

    # Recherche du document par _id
    station = collection.find_one({"_id": obj_id})

    if not station:
        return jsonify({
            "status": "error",
            "message": "Station introuvable."
        }), 404

    return jsonify({"status": "success", "data": serialize_doc(station)}), 200


# ── R2 : Filtrer les stations par seuil d'AQI ────────────────────────────────

@stations_bp.route("/filter/aqi", methods=["GET"])
def get_stations_by_aqi():
    """
    Retourne les stations dont l'indice de qualité de l'air (AQI) dépasse
    un seuil donné. Utile pour identifier les zones polluées.

    Paramètre de requête :
        min_aqi (int) : Seuil minimum d'AQI (défaut: 100)

    Exemple : GET /api/stations/filter/aqi?min_aqi=150

    Opérateur MongoDB utilisé : $gte (greater than or equal)
    """
    try:
        min_aqi = int(request.args.get("min_aqi", 100))
    except ValueError:
        return jsonify({
            "status": "error",
            "message": "Le paramètre min_aqi doit être un entier."
        }), 400

    # Filtre MongoDB : { "aqi": { "$gte": min_aqi } }
    # $gte est l'opérateur "supérieur ou égal à"
    stations = list(
        collection.find({"aqi": {"$gte": min_aqi}}).sort("aqi", -1)
    )

    return jsonify({
        "status": "success",
        "filter": f"aqi >= {min_aqi}",
        "count": len(stations),
        "data": [serialize_doc(s) for s in stations]
    }), 200


# ── R3 : Créer une nouvelle station ──────────────────────────────────────────

@stations_bp.route("/", methods=["POST"])
def create_station():
    """
    Insère un nouveau document station dans MongoDB.

    Body JSON attendu :
    {
        "station_id": "SN-DKR-001",
        "city": "Dakar",
        "country": "Senegal",
        "location": { "type": "Point", "coordinates": [-17.4441, 14.6928] },
        "measurements": { "co2_ppm": 412.5, "pm2_5": 38.2,
                          "temperature_c": 34.1, "humidity_pct": 71 },
        "aqi": 85,
        "status": "moderate"
    }

    Exemple : POST /api/stations/
    """
    data = request.get_json()

    # Validation des champs obligatoires
    required_fields = ["station_id", "city", "country", "location",
                       "measurements", "aqi"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        return jsonify({
            "status": "error",
            "message": f"Champs manquants : {', '.join(missing)}"
        }), 400

    # Ajout automatique du timestamp de création
    data["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Vérification de l'unicité du station_id
    if collection.find_one({"station_id": data["station_id"]}):
        return jsonify({
            "status": "error",
            "message": f"Une station avec l'ID '{data['station_id']}' existe déjà."
        }), 409

    # Insertion dans MongoDB — retourne un InsertOneResult
    result = collection.insert_one(data)

    return jsonify({
        "status": "success",
        "message": "Station créée avec succès.",
        "inserted_id": str(result.inserted_id)
    }), 201


# ── R3b : Mettre à jour les mesures d'une station ────────────────────────────

@stations_bp.route("/<station_id>", methods=["PATCH"])
def update_station(station_id):
    """
    Met à jour partiellement un document station (ex: nouvelles mesures).

    L'opérateur $set de MongoDB permet de modifier uniquement les champs
    fournis, sans écraser l'ensemble du document.

    Body JSON : { "aqi": 120, "measurements.co2_ppm": 430.2 }

    Exemple : PATCH /api/stations/665f1a2b3c4d5e6f7a8b9c0d
    """
    try:
        obj_id = ObjectId(station_id)
    except InvalidId:
        return jsonify({"status": "error", "message": "ObjectId invalide."}), 400

    data = request.get_json()

    if not data:
        return jsonify({
            "status": "error",
            "message": "Aucune donnée fournie dans le body."
        }), 400

    # $set : met à jour uniquement les champs spécifiés
    result = collection.update_one(
        {"_id": obj_id},
        {"$set": data}
    )

    if result.matched_count == 0:
        return jsonify({"status": "error", "message": "Station introuvable."}), 404

    return jsonify({
        "status": "success",
        "message": "Station mise à jour.",
        "modified_count": result.modified_count
    }), 200


# ── R3c : Supprimer une station ───────────────────────────────────────────────

@stations_bp.route("/<station_id>", methods=["DELETE"])
def delete_station(station_id):
    """
    Supprime définitivement une station de la base de données.

    Exemple : DELETE /api/stations/665f1a2b3c4d5e6f7a8b9c0d
    """
    try:
        obj_id = ObjectId(station_id)
    except InvalidId:
        return jsonify({"status": "error", "message": "ObjectId invalide."}), 400

    result = collection.delete_one({"_id": obj_id})

    if result.deleted_count == 0:
        return jsonify({"status": "error", "message": "Station introuvable."}), 404

    return jsonify({
        "status": "success",
        "message": "Station supprimée avec succès."
    }), 200
