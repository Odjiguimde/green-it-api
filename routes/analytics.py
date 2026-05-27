# ============================================================
# routes/analytics.py — Routes d'analyse avancée (Agrégations)
# ============================================================
# Ce module contient les requêtes avancées utilisant le
# framework d'agrégation de MongoDB ($match, $group, $sort)
# et les requêtes géospatiales ($near, index 2dsphere).
#
# Requêtes couvertes :
#   R4 — Requête géospatiale : stations proches d'un point GPS
#   R5 — Agrégation : moyenne CO₂ et AQI par ville
#         sur une période configurable
# ============================================================
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone
from config import get_db

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")

# ── R4 : Stations géographiquement proches d'un point GPS ────────────────────
@analytics_bp.route("/nearby", methods=["GET"])
def get_nearby_stations():
    try:
        collection = get_db()["stations"] # Appel dynamique ici
        lng = float(request.args.get("lng"))
        lat = float(request.args.get("lat"))
        radius = int(request.args.get("radius", 50000))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Paramètres invalides. 'lng' et 'lat' (float) sont requis."}), 400

    query = {
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "$maxDistance": radius
            }
        }
    }

    try:
        stations = list(collection.find(query))
        for s in stations:
            s["_id"] = str(s["_id"])
        return jsonify({"status": "success", "reference_point": {"longitude": lng, "latitude": lat}, "radius_m": radius, "count": len(stations), "data": stations}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "hint": "Vérifiez que l'index 2dsphere est créé sur le champ 'location'."}), 500

# ── R5 : Agrégation — Statistiques par ville sur N derniers jours ─────────────
@analytics_bp.route("/city-stats", methods=["GET"])
def get_city_statistics():
    try:
        collection = get_db()["stations"] # Appel dynamique ici
        days = int(request.args.get("days", 30))
        if days < 1 or days > 365:
            raise ValueError
    except ValueError:
        return jsonify({"status": "error", "message": "Le paramètre 'days' doit être un entier entre 1 et 365."}), 400

    date_limit = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    pipeline = [
        {"$match": {"timestamp": {"$gte": date_limit}}},
        {"$group": {
            "_id": "$city",
            "avg_aqi": {"$avg": "$aqi"},
            "avg_co2_ppm": {"$avg": "$measurements.co2_ppm"},
            "avg_pm25": {"$avg": "$measurements.pm2_5"},
            "measurement_count": {"$sum": 1}
        }},
        {"$sort": {"avg_aqi": -1}},
        {"$project": {
            "_id": 0,
            "city": "$_id",
            "avg_aqi": {"$round": ["$avg_aqi", 2]},
            "avg_co2_ppm": {"$round": ["$avg_co2_ppm", 2]},
            "avg_pm25": {"$round": ["$avg_pm25", 2]},
            "measurement_count": 1
        }}
    ]

    try:
        results = list(collection.aggregate(pipeline))
        return jsonify({"status": "success", "period_days": days, "date_from": date_limit, "city_count": len(results), "data": results}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ── BONUS : Seed — Insérer des données de test ───────────────────────────────
@analytics_bp.route("/seed", methods=["POST"])
def seed_database():
    collection = get_db()["stations"] # Appel dynamique ici
    sample_data = [
        {
            "station_id": "SN-DKR-001",
            "city": "Dakar",
            "country": "Senegal",
            "location": {"type": "Point", "coordinates": [-17.4441, 14.6928]},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "measurements": {"co2_ppm": 412.5, "pm2_5": 38.2, "temperature_c": 34.1, "humidity_pct": 71},
            "aqi": 85,
            "status": "moderate"
        },
        {
            "station_id": "SN-THI-001",
            "city": "Thiès",
            "country": "Senegal",
            "location": {"type": "Point", "coordinates": [-16.9241, 14.7910]},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "measurements": {"co2_ppm": 398.1, "pm2_5": 22.5, "temperature_c": 31.8, "humidity_pct": 65},
            "aqi": 60,
            "status": "good"
        },
        {
            "station_id": "SN-ZIG-001",
            "city": "Ziguinchor",
            "country": "Senegal",
            "location": {"type": "Point", "coordinates": [-16.2719, 12.5605]},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "measurements": {"co2_ppm": 425.3, "pm2_5": 55.0, "temperature_c": 36.2, "humidity_pct": 80},
            "aqi": 142,
            "status": "unhealthy"
        },
        {
            "station_id": "SN-SLM-001",
            "city": "Saint-Louis",
            "country": "Senegal",
            "location": {"type": "Point", "coordinates": [-16.5085, 16.0179]},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "measurements": {"co2_ppm": 405.7, "pm2_5": 30.1, "temperature_c": 33.4, "humidity_pct": 68},
            "aqi": 101,
            "status": "unhealthy_sensitive"
        },
        {
            "station_id": "SN-DKR-002",
            "city": "Dakar",
            "country": "Senegal",
            "location": {"type": "Point", "coordinates": [-17.3660, 14.7247]},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "measurements": {"co2_ppm": 430.8, "pm2_5": 48.9, "temperature_c": 35.0, "humidity_pct": 74},
            "aqi": 118,
            "status": "unhealthy_sensitive"
        }
    ]

    ids = [d["station_id"] for d in sample_data]
    collection.delete_many({"station_id": {"$in": ids}})
    result = collection.insert_many(sample_data)

    return jsonify({"status": "success", "message": f"{len(result.inserted_ids)} stations insérées.", "inserted_ids": [str(i) for i in result.inserted_ids]}), 201
