from flask import Blueprint, request, jsonify
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from config import get_db

stations_bp = Blueprint("stations", __name__, url_prefix="/api/stations")

# ── Utilitaire ────────────────────────────────────────────────────────────────
def serialize_doc(doc):
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc

# ── R0 : Lister toutes les stations ──────────────────────────────────────────
@stations_bp.route("/", methods=["GET"])
def get_all_stations():
    try:
        collection = get_db()["stations"] # Appel dynamique ici
        page = max(1, int(request.args.get("page", 1)))
        limit = min(100, max(1, int(request.args.get("limit", 10))))
        skip = (page - 1) * limit

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
    try:
        collection = get_db()["stations"] # Appel dynamique ici
        obj_id = ObjectId(station_id)
    except InvalidId:
        return jsonify({"status": "error", "message": f"'{station_id}' n'est pas un ObjectId valide."}), 400

    station = collection.find_one({"_id": obj_id})
    if not station:
        return jsonify({"status": "error", "message": "Station introuvable."}), 404

    return jsonify({"status": "success", "data": serialize_doc(station)}), 200

# ── R2 : Filtrer les stations par seuil d'AQI ────────────────────────────────
@stations_bp.route("/filter/aqi", methods=["GET"])
def get_stations_by_aqi():
    try:
        collection = get_db()["stations"] # Appel dynamique ici
        min_aqi = int(request.args.get("min_aqi", 100))
    except ValueError:
        return jsonify({"status": "error", "message": "Le paramètre min_aqi doit être un entier."}), 400

    stations = list(collection.find({"aqi": {"$gte": min_aqi}}).sort("aqi", -1))
    return jsonify({"status": "success", "filter": f"aqi >= {min_aqi}", "count": len(stations), "data": [serialize_doc(s) for s in stations]}), 200

# ── R3 : Créer une nouvelle station ──────────────────────────────────────────
@stations_bp.route("/", methods=["POST"])
def create_station():
    collection = get_db()["stations"] # Appel dynamique ici
    data = request.get_json()
    required_fields = ["station_id", "city", "country", "location", "measurements", "aqi"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        return jsonify({"status": "error", "message": f"Champs manquants : {', '.join(missing)}"}), 400

    data["timestamp"] = datetime.now(timezone.utc).isoformat()

    if collection.find_one({"station_id": data["station_id"]}):
        return jsonify({"status": "error", "message": f"Une station avec l'ID '{data['station_id']}' existe déjà."}), 409

    result = collection.insert_one(data)
    return jsonify({"status": "success", "message": "Station créée avec succès.", "inserted_id": str(result.inserted_id)}), 201

# ── R3b : Mettre à jour les mesures d'une station ────────────────────────────
@stations_bp.route("/<station_id>", methods=["PATCH"])
def update_station(station_id):
    try:
        collection = get_db()["stations"] # Appel dynamique ici
        obj_id = ObjectId(station_id)
    except InvalidId:
        return jsonify({"status": "error", "message": "ObjectId invalide."}), 400

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Aucune donnée fournie dans le body."}), 400

    result = collection.update_one({"_id": obj_id}, {"$set": data})
    if result.matched_count == 0:
        return jsonify({"status": "error", "message": "Station introuvable."}), 404

    return jsonify({"status": "success", "message": "Station mise à jour.", "modified_count": result.modified_count}), 200

# ── R3c : Supprimer une station ───────────────────────────────────────────────
@stations_bp.route("/<station_id>", methods=["DELETE"])
def delete_station(station_id):
    try:
        collection = get_db()["stations"] # Appel dynamique ici
        obj_id = ObjectId(station_id)
    except InvalidId:
        return jsonify({"status": "error", "message": "ObjectId invalide."}), 400

    result = collection.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        return jsonify({"status": "error", "message": "Station introuvable."}), 404

    return jsonify({"status": "success", "message": "Station supprimée avec succès."}), 200
