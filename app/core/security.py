def setup_security_headers(app):
    """
    Configura cabeceras HTTP de seguridad para cumplir con estándares
    de SonarQube, OWASP y auditorías de Snyk.
    """

    from urllib.parse import urlsplit

    @app.after_request
    def add_security_headers(response):
        # Previene ataques de clickjacking
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # Previene ataques de MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Política de Referrer estricta
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (CSP)
        firebase_host = app.config.get('FIREBASE_AUTH_DOMAIN', '')
        valid_firebase_host = urlsplit('https://' + firebase_host).hostname == firebase_host and firebase_host.endswith('.firebaseapp.com')
        auth_frame = f'https://{firebase_host}' if valid_firebase_host and app.config.get('AUTH_PROVIDER') == 'firebase' else "'none'"
        firebase_scripts = ' https://apis.google.com' if app.config.get('AUTH_PROVIDER') == 'firebase' else ''
        firebase_connect = ' https://identitytoolkit.googleapis.com https://securetoken.googleapis.com https://www.googleapis.com' if app.config.get('AUTH_PROVIDER') == 'firebase' else ''
        csp_directives = (
            "default-src 'self'; "
            f"script-src 'self'{firebase_scripts}; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob: https:; "
            f"connect-src 'self'{firebase_connect}; "
            f"frame-src {auth_frame}; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp_directives

        return response
