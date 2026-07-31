"""
app/infra/logging_config.py
----------------------------
Configura o sistema de logging da aplicação.

Centralizar o logging aqui garante que todos os módulos usem
o mesmo formato, nível e destino de log, facilitando a
observabilidade e a depuração em qualquer ambiente.
"""

import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """
    Configura o logging global da aplicação.

    - Em desenvolvimento: nível DEBUG para ver tudo.
    - Em outros ambientes: nível INFO para produção limpa.
    - Formato padronizado com timestamp, nível e nome do módulo.
    - Saída para stdout (compatível com containers e ferramentas de log).
    """

    # Define o nível de log com base no ambiente
    log_level = logging.DEBUG if settings.APP_ENV == "development" else logging.INFO

    # Formato legível para humanos e ferramentas de log
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configura o handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))

    # Configura o logger raiz da aplicação
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()  # Remove handlers duplicados ao recarregar
    root_logger.addHandler(handler)

    # Silencia logs muito verbosos de bibliotecas externas em produção
    if settings.APP_ENV != "development":
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        f"Logging configurado | ENV={settings.APP_ENV} | LEVEL={logging.getLevelName(log_level)}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger nomeado para uso em qualquer módulo.

    Uso:
        logger = get_logger(__name__)
        logger.info("Mensagem de exemplo")

    Args:
        name: normalmente __name__ do módulo chamador.

    Returns:
        Logger configurado com o nome fornecido.
    """
    return logging.getLogger(name)
