from django.contrib.gis.geoip2 import GeoIP2
from django.conf import settings

class GeoLocationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.geo = GeoIP2()
        # En développement, tu peux utiliser une IP de test
        # Change cette IP pour tester différentes localisations
        self.test_ip = getattr(settings, 'GEOIP_TEST_IP', None)

    def __call__(self, request):

        # Si déjà détecté → on ne refait rien
        if not request.session.get("country"):
            ip = self.get_client_ip(request)
            
            # En développement local (127.0.0.1), utiliser une IP de test si configurée
            if ip == "127.0.0.1" and self.test_ip and settings.DEBUG:
                ip = self.test_ip

            try:
                data = self.geo.city(ip)
                request.session["country"] = data.get("country_name", "Votre pays")
                request.session["country_code"] = data.get("country_code", "")
                request.session["city"] = data.get("city") or "Votre ville"
            except Exception:
                request.session["country"] = "Votre pays"
                request.session["city"] = "Votre ville"

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get("REMOTE_ADDR")

# =============================================
# POUR TESTER EN DÉVELOPPEMENT :
# Ajoute dans settings.py :
#   GEOIP_TEST_IP = "197.159.0.1"  # IP du Togo (exemple)
#   ou d'autres IPs selon le pays que tu veux tester
# =============================================
# IPs d'exemple par pays :
#   France       : 185.102.113.0
#   Belgique     : 193.190.62.0
#   Canada       : 99.254.200.0
#   États-Unis   : 8.8.8.8
#   Togo         : 197.159.0.1
# ============================================
