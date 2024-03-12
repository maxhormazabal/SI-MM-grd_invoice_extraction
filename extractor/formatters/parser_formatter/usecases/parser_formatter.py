from extractor.common.usecases.base import BaseUseCase
from ..services.file_utils import read_files_list, dump_io_data


class ParserFormatterUseCase(BaseUseCase):
    def __init__(
        self,
        elements_file_list: list[str],
        lines_file_list: list[str],
        output_file: str,
    ):
        """Initialization of parameters

        Reads files and elements that will conform a json to the parser

        Args:
          elements_file_list: list of paths to files with elements
          lines_file_list: list of path to files with lines
          output_file: path to the output file that will contain the result

          config: dict with configuration
          input_doc: dict with the parser input format

        """

        super().__init__()

        self.data_list = read_files_list(elements_file_list, lines_file_list)

        self.output_file = output_file

    def execute(self):
        """Generates output file"""

        dump_io_data(self.data_list, self.output_file)
