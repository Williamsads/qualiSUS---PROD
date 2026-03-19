from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

# Limitador de Taxa de Requisições (Anti Brute-Force / Scraping)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "200 per hour"]
)

# Proteção CSRF (Cross-Site Request Forgery)
# Protege todos os endpoints de mutação contra requisições forjadas cross-origin
csrf = CSRFProtect()
