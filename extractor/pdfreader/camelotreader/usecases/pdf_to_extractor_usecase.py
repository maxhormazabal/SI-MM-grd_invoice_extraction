import logging
import os
import sys
import time

# para ejecutar con pycharm-eliminar si da problemas
# sys.path.append(os.path.abspath("..."))


from extractor.common.cli.logging import get_elapsed_time_message
from extractor.common.usecases.base import BaseUseCase
from ..services.blobber import GenerateBlob

logger = logging.getLogger("pdfreader.camelot")


class PDFExtractorUseCase(BaseUseCase):
    def __init__(self, config: dict, input_file: dict):
        """Initialization of parameters

        Args:
          config: dict with configuration
          input_file: path to the pdf file

        """

        super().__init__()
        self.config = config
        self.input_file = input_file
        self.result = None

    def execute(self):
        """Extracts information from a PDF and generates a extractor file format that can serve as input to classifiers and parsers"""

        logger.debug("Processing document with camelot")
        start_time = time.time()

        processor = GenerateBlob(self.config, self.input_file)
        self.result = processor.generate_extractor()

        logger.debug(get_elapsed_time_message("process with camelot", start_time))

        return self.result
