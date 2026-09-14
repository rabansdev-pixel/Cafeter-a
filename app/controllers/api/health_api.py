from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Endpoint de salud para Docker HEALTHCHECK y orquestación."""
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "cafeteria-especialidad",
                "version": "1.0.0",
            }
        ),
        200,
    )
