import logging

import app.infra.logging_config as logging_config


def test_setup_logging_uses_debug_in_development(monkeypatch):
    monkeypatch.setattr(logging_config.settings, "APP_ENV", "development")

    logging_config.setup_logging()

    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 1
    assert root_logger.handlers[0].level == logging.DEBUG


def test_setup_logging_uses_info_and_quiets_external_libraries(monkeypatch):
    monkeypatch.setattr(logging_config.settings, "APP_ENV", "production")

    logging_config.setup_logging()

    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
    assert root_logger.handlers[0].level == logging.INFO
    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("openai").level == logging.WARNING


def test_get_logger_returns_named_logger():
    logger = logging_config.get_logger("access_fit.test")

    assert logger is logging.getLogger("access_fit.test")
