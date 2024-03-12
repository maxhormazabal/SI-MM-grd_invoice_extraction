import logging
from extractor.common.infraestructure.ElasticClient import OCRConnection

logger = logging.getLogger("ocr_controller")


def get_ocr_client(config):
    return OCRConnection(config)
