import logging
from .parse_utils import LTText
from .stream import Stream

DEFAULT_PAGE_WIDTH = 842
DEFAULT_PAGE_HEIGHT = 595

logger = logging.getLogger("format.ocr")


def _get_page_object(
    element_list: list[dict],
    row_list: list[dict],
    page_idx: int,
    source: str,
    separator=" [SEP] ",
) -> dict:
    """Get page object

    Args:
      element_list: list of elements
      row_list: list of rows
      page_idx: index of the page
      source: name of the source
      separator: separator between elements in a row

    Returns:
      the page object

    """

    elem_dump_list = []

    for _elem in element_list:
        elem_dump_list.append({"text": _elem["text"], "labels": [], "orig": _elem})

    row_dump_list = []
    for _row in row_list:
        elem_text_list = []

        for _elem in _row:
            elem_text_list.append(_elem["text"])

        row_dump_list.append(
            {"text": separator.join(elem_text_list), "labels": [], "orig": _row}
        )

    _page = {
        "source": source,
        "page": page_idx,
        "elements": elem_dump_list,
        "lines": row_dump_list,
    }

    return _page


def _extract_lines(
    element_list: list[dict], row_tol: int, page_height: int
) -> list[dict]:
    """Get the lines of a document

    Args:
      element_list: list of elements in a document
      row_tol: row tolerance
      page_height: height of the page

    Returns:
      the list of lines of a document

    """

    element_dict = {}

    horizontal_text = []

    for _elem in element_list:
        elem_key = "{}_{}_{}_{}".format(
            _elem["x0"], _elem["y0"], _elem["x1"], _elem["y1"]
        )

        element_dict[elem_key] = _elem["id"]
        lt = LTText(_elem["text"], _elem["x0"], _elem["y0"], _elem["x1"], _elem["y1"])
        horizontal_text.append(lt)

    rows_grouped = Stream._group_rows(horizontal_text, row_tol)
    Stream._join_rows(rows_grouped, page_height, 0)

    row_list = []

    for _row in rows_grouped:
        elem_list = []

        for _elem in _row:
            elem_key = "{}_{}_{}_{}".format(_elem.x0, _elem.y0, _elem.x1, _elem.y1)
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

    return row_list


def _translate_vertices(bb: dict, page_width: int, page_height: int) -> dict:
    """Translate vertices from boundingbox

    Args:
      bb : bounding box
      page_width: width of the page
      page_height: height of the page

    """

    x_list = [_vert["x"] for _vert in bb]
    y_list = [(1 - _vert["y"]) for _vert in bb]

    # Denormalizing verticies
    x0 = min(x_list) * page_width
    y0 = min(y_list) * page_height
    x1 = max(x_list) * page_width
    y1 = max(y_list) * page_height

    return x0, y0, x1, y1


def _extract_elements(
    _page: list[dict], page_width: int, page_height: int, index_elem: int
) -> dict:
    """Extract elements from a page

    Args:
       _page: page element
       page_width: width of the page
       page_height: height of the page
       index_elem: index of elements

    """
    element_list = []

    if "blocks" in _page:
        for _block in _page["blocks"]:
            if "paragraphs" in _block:
                for _parag in _block["paragraphs"]:
                    bb = _parag["boundingBox"]["normalizedVertices"]

                    x0, y0, x1, y1 = _translate_vertices(bb, page_width, page_height)

                    word_list = []

                    if "words" in _parag:
                        for _word in _parag["words"]:
                            word_list.append(_word["text"])
                            word_list.append(" ")

                    text = "".join(word_list).strip()

                    if len(text) > 0:
                        element = {
                            "text": text,
                            "x0": x0,
                            "y0": y0,
                            "x1": x1,
                            "y1": y1,
                            "id": index_elem,
                        }

                        element_list.append(element)

                        index_elem += 1

    return element_list


def parse_ocr_content(config: dict, input_doc: dict, page_widhts, page_heights):
    """Annotate products

    Args:
        config: dictionary with the configuration of the parser
        input_doc: input file

    """

    source = input_doc["inputConfig"]["docPath"]

    index_elem = 0

    row_tol = config["row_tol"]

    page_object_list = []
    for page_idx, _page in enumerate(
        input_doc["responses"]["fullTextAnnotation"]["pages"]
    ):
        page_width = (
            page_widhts[page_idx] if len(page_widhts) > page_idx else DEFAULT_PAGE_WIDTH
        )
        page_height = (
            page_heights[page_idx]
            if len(page_heights) > page_idx
            else DEFAULT_PAGE_HEIGHT
        )

        element_list = _extract_elements(_page, page_width, page_height, index_elem)

        # update index of elements
        index_elem += len(element_list)

        # obtain lines
        row_list = _extract_lines(element_list, row_tol, page_height)

        page_object = _get_page_object(element_list, row_list, page_idx, source)
        page_object_list.append(page_object)

    return {"data": page_object_list, "annotations": {}}
