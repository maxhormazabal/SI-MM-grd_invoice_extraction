import logging

logger = logging.getLogger("infra.ocr")


class OCRConnection:
    def __init__(self, ip, port, user, password):
        logger.debug("Creating OCR connection")
