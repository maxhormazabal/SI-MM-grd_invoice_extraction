import logging
import os
import json
from camelot.handlers import PDFHandler
from PyPDF2 import PdfFileReader, PdfFileWriter
from camelot.utils import (
    get_page_layout,
    get_text_objects,
    get_rotation,
    is_url,
    download_url,
)
from camelot.parsers.stream import Stream

logger = logging.getLogger("pdfreader.camelot")


class TextBlob(PDFHandler):
    """ """

    def _dump(self, file_path, page, output_path):

        basename = os.path.basename(file_path)

        with open(file_path, "rb") as fileobj:
            infile = PdfFileReader(fileobj, strict=False)

            if infile.isEncrypted:
                infile.decrypt(self.password)

            fpath = os.path.join(output_path, "{0}-page-{1}.pdf".format(basename, page))
            froot, fext = os.path.splitext(fpath)

            p = infile.getPage(page - 1)
            outfile = PdfFileWriter()
            outfile.addPage(p)

            with open(fpath, "wb") as f:
                outfile.write(f)

            layout, dim = get_page_layout(fpath, detect_vertical=False)

            get_text_objects(layout, ltype="char")
            horizontal_text = get_text_objects(layout, ltype="horizontal_text")
            vertical_text = get_text_objects(layout, ltype="vertical_text")

            fdson = os.path.join(
                output_path, "{0}-page-{1}.json".format(basename, page)
            )

            logger.trace("DIM {}".format(dim))

            page_dict = {}
            page_dict["dimensions"] = [dim[0], dim[1]]
            page_dict["pdf_width"] = dim[0]
            page_dict["pdf_height"] = dim[1]

            page_dict["horizontal"] = []
            page_dict["vertical"] = []

            horizontal_text.sort(key=lambda d: (-d.y0, d.x0))

            index_elem = 0
            element_dict = {}

            for _t in horizontal_text:
                page_dict["horizontal"].append(
                    {
                        "text": _t.get_text(),
                        "x0": _t.x0,
                        "y0": _t.y0,
                        "x1": _t.x1,
                        "y1": _t.y1,
                        "id": index_elem,
                    }
                )

                element_dict[
                    "{}_{}_{}_{}".format(_t.x0, _t.y0, _t.x1, _t.y1)
                ] = index_elem

                index_elem += 1

            for _t in vertical_text:
                page_dict["vertical"].append(
                    {
                        "text": _t.get_text(),
                        "x0": _t.x0,
                        "y0": _t.y0,
                        "x1": _t.x1,
                        "y1": _t.y1,
                        "id": index_elem,
                    }
                )

                element_dict[
                    "{}_{}_{}_{}".format(_t.x0, _t.y0, _t.x1, _t.y1)
                ] = index_elem

                index_elem += 1

            # order the elements in horizontal list by their y0

            # page_dict["horizontal"].sort(key=lambda d: (-d['y0'], d["x0"]))

            rows_grouped = Stream._group_rows(horizontal_text, self.row_tol)
            rows = Stream._join_rows(rows_grouped, dim[1], 0)

            logger.trace("Rows Grouped {}".format(rows_grouped))
            logger.trace("rows {}".format(rows))

            row_list = []

            page_dict["horizontal_lines"] = []
            for _row in rows_grouped:
                elem_list = []

                for _elem in _row:
                    elem_key = "{}_{}_{}_{}".format(
                        _elem.x0, _elem.y0, _elem.x1, _elem.y1
                    )

                    key_id_elem = element_dict[elem_key]

                    elem_list.append(
                        {
                            "text": _elem.get_text(),
                            "x0": _elem.x0,
                            "y0": _elem.y0,
                            "x1": _elem.x1,
                            "y1": _elem.y1,
                            "id": key_id_elem,
                        }
                    )

                row_list.append(elem_list)

            page_dict["rows_grouped"] = row_list

            with open(fdson, "w+") as f_out:
                f_out.write("{}\n".format(json.dumps(page_dict)))

    def dump_pages(self, output_path):

        for page in self.pages:
            self._dump(self.filepath, page, output_path)

    def check(self):
        logger.trace("Pages ", self.pages)

    def __init__(self, file_path, pages="1", password=None, row_tol=5):
        """Initial stuff"""

        self.row_tol = row_tol
        super().__init__(file_path, pages, password)
