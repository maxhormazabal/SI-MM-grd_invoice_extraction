import os
import re
import logging
import tempfile
import shutil
import json
from .line_extractor import LineExtractor
from .text_blob import TextBlob
from .pdfreader_exceptions import PDFReaderError


logger = logging.getLogger("pdfreader.camelot")


class GenerateBlob(object):
    """Generate a json with lines and elements"""

    def _generate_elements(self, json_list: dict) -> list[list[dict]]:
        """Extract elements from each json

        Args:
          json_list: list of json

        Returns:
          the list of elements per file (list of list of elements)

        """

        result_file_list = []

        for _json in json_list:

            result_element_list = []

            extractor = LineExtractor(self.config)

            line_list, orig_list = extractor.extract_elements(_json)

            for _line, _orig in zip(line_list, orig_list):
                if (
                    "default_label" in self.config
                    and self.config["default_label"] is not None
                ):
                    sample = {
                        "text": _line,
                        "labels": [self.config["default_label"]],
                        "orig": _orig,
                    }

                else:
                    sample = {"text": _line, "labels": [], "orig": _orig}

                result_element_list.append(sample)

            result_file_list.append(result_element_list)

        return result_file_list

    def _generate_lines(self, json_list: dict) -> list[list[dict]]:
        """Extract elements from each json

        Args:
          json_list: list of json

        Returns:
          the list of elements per file (list of list of elements)

        """

        result_file_list = []

        for _json in json_list:

            result_lines_list = []

            extractor = LineExtractor(self.config)

            lines_list, orig_list = extractor.extract_lines(_json)

            for _line, _orig in zip(lines_list, orig_list):

                if (
                    "default_label" in self.config
                    and self.config["default_label"] is not None
                ):

                    sample = {
                        "text": _line,
                        "labels": [self.config["default_label"]],
                        "orig": _orig,
                    }

                else:
                    sample = {"text": _line, "labels": [], "orig": _orig}

                result_lines_list.append(sample)

            result_file_list.append(result_lines_list)

        return result_file_list

    def _generate_files(self) -> list[str, dict]:
        """Generate files for element and line extraction

        Returns:
          a list of file names, a list of jsons with the information of the files

        """

        dirpath = tempfile.mkdtemp()
        blobber = TextBlob(self.input_path, pages="all", row_tol=self.config["row_tol"])

        pages = blobber.pages

        for i in pages:
            blobber._save_page(self.input_path, i, dirpath)

        blobber.check()
        blobber.dump_pages(dirpath)

        # read the json files
        json_files = [
            pos_json for pos_json in os.listdir(dirpath) if pos_json.endswith(".json")
        ]
        json_files.sort(key=self.natural_sort_key)
        json_readings = []

        for _file in json_files:
            _ndpath = os.path.join(dirpath, _file)

            with open(_ndpath, "r+") as f_in:
                _json = json.load(f_in)
                json_readings.append(_json)

        shutil.rmtree(dirpath)

        return json_files, json_readings

    def generate_extractor(self) -> dict:
        """Generate extractor file from

        Returns:
          a json with the extractor format (ready for the parsers)

        """

        file_name_list, json_list = self._generate_files()

        elements_file_list = self._generate_elements(json_list)
        lines_file_list = self._generate_lines(json_list)

        data_list = []

        source = os.path.basename(self.input_path)

        if (
            elements_file_list is not None
            and lines_file_list is not None
            and len(elements_file_list) == len(lines_file_list)
        ):

            for idx in range(len(file_name_list)):
                _elems_list = elements_file_list[idx]
                _lines_list = lines_file_list[idx]
                _width = json_list[idx].get("pdf_width")
                _height = json_list[idx].get("pdf_height")

                data_list.append(
                    {
                        "source": source,
                        "page": idx,
                        "elements": _elems_list,
                        "lines": _lines_list,
                        "height": _height,
                        "width": _width,
                    }
                )

        else:
            raise PDFReaderError("Exception whilst processing input PDF file")

        _json = {"data": data_list, "annotations": {}}

        return _json

    def natural_sort_key(self, s):
        _nsre = re.compile("([0-9]+)")

        return [
            int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)
        ]

    def __init__(self, config, input_path):
        """Initialization stuff"""

        self.input_path = input_path
        self.config = config
