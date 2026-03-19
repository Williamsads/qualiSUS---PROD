from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Inicializa o Limitador de Taxa de Requisições (Proteção Contra Brute-Force / Scraping)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "200 per hour"] # Limite genérico para não travar o sistema inteiro, customizaremos nas rotas
)
