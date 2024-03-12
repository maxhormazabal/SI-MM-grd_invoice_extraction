import logging


logger = logging.getLogger("pdfreader.camelot")


class LineExtractor(object):
    """Line extractor"""

    def extract_elements(self, _json):
        """Extract elements from a json"""

        full_elements = []
        orig_data = []

        elem_list = _json["horizontal"]

        for _t in ["horizontal", "vertical"]:
            elem_list = _json[_t]

            for _elem in elem_list:
                full_elements.append(_elem["text"])
                orig_data.append(_elem)

        return full_elements, orig_data

    def extract_lines(self, _json):
        """Extract lines from a json"""

        full_lines = []
        orig_data = []
        rows = _json["rows_grouped"]

        for _row in rows:
            text_list = [_elem["text"] for _elem in _row]

            orig_line = [_elem for _elem in _row]

            _line = self.config["element_separator"].join(text_list)
            full_lines.append(_line)
            orig_data.append(orig_line)

        return full_lines, orig_data

    def __init__(self, config):
        self.config = config
