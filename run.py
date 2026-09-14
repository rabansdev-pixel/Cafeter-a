import os
from app import create_app

env = os.getenv("APP_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    # Por seguridad, por defecto solo vincula a loopback (127.0.0.1)
    # En Docker, se puede sobreescribir configurando HOST=0.0.0.0
    host = os.getenv("HOST", "127.0.0.1")
    is_dev = env == "development"
    debug_mode = is_dev and os.getenv("FLASK_DEBUG", "0") == "1"

    print(f"☕ Atelier Café iniciado en http://{host}:{port} [Modo: {env}]")
    app.run(host=host, port=port, debug=debug_mode)
