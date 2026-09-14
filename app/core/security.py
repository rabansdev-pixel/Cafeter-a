def setup_security_headers(app):
    """
    Configura cabeceras HTTP de seguridad para cumplir con estándares
    de SonarQube, OWASP y auditorías de Snyk.
    """

    @app.after_request
    def add_security_headers(response):
        # Previene ataques de clickjacking
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # Previene ataques de MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Política de Referrer estricta
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (CSP)
        csp_directives = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp_directives

        return response
