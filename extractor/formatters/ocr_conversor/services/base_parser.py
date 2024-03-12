import os
import json

from .parse_utils import LTText


class BaseParser(object):
    """Defines a base parser."""

    def _generate_layout(self, filename, layout_kwargs):

        self.filename = filename
        self.layout_kwargs = layout_kwargs
        self.images = None

        with open(filename, "r") as f_in:
            _json = json.load(f_in)

        self.horizontal_text = [
            LTText(t["text"], t["x0"], t["y0"], t["x1"], t["y1"])
            for t in _json["horizontal"]
        ]
        self.vertical_text = [
            LTText(t["text"], t["x0"], t["y0"], t["x1"], t["y1"])
            for t in _json["vertical"]
        ]
        self.pdf_width = _json["pdf_width"]
        self.pdf_height = _json["pdf_height"]
        self.rootname, __ = os.path.splitext(self.filename)
