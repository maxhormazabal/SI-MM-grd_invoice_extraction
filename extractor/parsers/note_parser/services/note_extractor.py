import logging
import re

from extractor.common.services.Box import Box, vertical_distance_boxes

logger = logging.getLogger("parser.note")


NOTE_TAG = "NOTE"


def _get_elements_ids_with_note(elem_list: list[dict]) -> list[int]:
    """Returns the list of ids of elements with note detections

    Args:
       elem_list: list of elements of a document

    Returns:
      the list of ids of the elements with note tag

    """

    id_element_list = []

    for _elem in elem_list:
        if NOTE_TAG in _elem["labels"]:
            id_element_list.append(_elem["orig"]["id"])

    return id_element_list


def _get_line_idx_with_note_elements(
    lines_list: list[dict], id_element_list: list[dict]
) -> list[int]:
    """Get the ids of the lines with note elements

    Args:
      lines_list: list of lines of a document
      id_element_list: list of ids of elements with note annotations

    """

    id_lines_list = []

    for idx, _line in enumerate(lines_list):
        for _elem in _line["orig"]:
            if _elem["id"] in id_element_list:
                id_lines_list.append(idx)

    return id_lines_list


def get_lines_distance(last_line, current_line):

    last_line_box = Box(last_line)
    current_line_box = Box(current_line)
    return vertical_distance_boxes(last_line_box, current_line_box, scope="bottom")


def _merge_note_lines(lines_box_list: dict[int], max_line_jumps: int):
    """Get the lines in the notes

    Args:
      lines_id_list: list of ids of the lines
      max_line_jumps: maximum number of jumps betwen note lines

    Returns:
      a dict with note ids and the lines that are contained in each note

    """

    note_dict = {}
    current_note_idx = 0

    last_line_notes = None
    box_last_line = None

    for idx in lines_box_list:
        if last_line_notes is None:
            note_dict[current_note_idx] = [idx]
            last_line_notes = idx
            box_last_line = lines_box_list[idx]

        elif is_together(box_last_line, lines_box_list[idx], max_line_jumps):
            # add to the current note and those in between

            for _off in range(idx - last_line_notes):
                _new_idx = last_line_notes + _off + 1

                note_dict[current_note_idx].append(_new_idx)

            last_line_notes = idx
            box_last_line = lines_box_list[idx]

        else:
            # add a new note
            current_note_idx += 1
            note_dict[current_note_idx] = [idx]
            last_line_notes = idx
            box_last_line = lines_box_list[idx]

    return note_dict


def is_together(box_last_line, lines_box_list, max_line_jumps):

    distance = vertical_distance_boxes(
        box_last_line, lines_box_list, scope="bottom", abs_value=True
    )
    h = lines_box_list.height
    threshold = max_line_jumps * h
    if distance <= threshold:
        return True
    return False


def _get_note_bbs(
    note_dict: dict, lines_list: list[dict], elements_id_list: list[dict]
) -> dict:
    """Get bounding boxes of notes

    Args
      note_dict: dict with note ids and a list of lines that are part of the note
      lines_list: list of lines of a document
      elements_id_list: list of id elements with note labels

    """

    note_bb_dict = {}

    for _note_id in note_dict:
        note_bb_list = []

        note_id_list = note_dict[_note_id]

        for idx in note_id_list:
            elem_list = lines_list[idx]["orig"]
            for _elem in elem_list:
                _id_elem = _elem["id"]

                if _id_elem in elements_id_list:
                    note_bb_list.append(
                        [_elem["x0"], _elem["y0"], _elem["x1"], _elem["y1"]]
                    )

        note_bb = [
            min([_note[0] for _note in note_bb_list]),
            max([_note[1] for _note in note_bb_list]),
            max([_note[2] for _note in note_bb_list]),
            min([_note[3] for _note in note_bb_list]),
        ]

        note_bb_dict[_note_id] = note_bb

    return note_bb_dict


def _get_note_elements_in_bb(
    note_bb_dict: dict, elements_list: list[dict]
) -> list[list]:
    """Obtain the list of elements in a note

    Args:
      note_bb_dict: dictionary with boundingboxes (x0, y0, x1, y1) per note id
      elements_list: list of elements in a document

    Returns:
      the list of elements in a note

    """

    elements_note_list = []

    for _note_idx in note_bb_dict:
        it_elements = []
        bb = note_bb_dict[_note_idx]
        x0, y0, x1, y1 = bb

        for _elem in elements_list:

            if (
                _elem["orig"]["x0"] >= x0
                and _elem["orig"]["y0"] <= y0
                and _elem["orig"]["x1"] <= x1
                and _elem["orig"]["y1"] >= y1
            ):

                it_elements.append(_elem)

        elements_note_list.append(it_elements)

    return elements_note_list


def _detect_note_boundingboxes(data: dict, max_line_jumps: int) -> list[dict]:
    """Detect bounding boxes of notes

    Args:
      data: dict with data
      max_line_jumps: maximum number of jumps betwen note lines

    Returns:
      the list of boundingboxes in a dict with note detections

    """

    elem_id_list = _get_elements_ids_with_note(data["elements"])
    lines_id_list = _get_line_idx_with_note_elements(data["lines"], elem_id_list)
    bbox_of_lines = _get_bboxes_of_lines(lines_id_list, data["lines"], data["elements"])
    box_of_lines = _get_box_of_lines(lines_id_list, bbox_of_lines)
    note_dict = _merge_note_lines(box_of_lines, max_line_jumps)
    note_bb_dict = _get_note_bbs(note_dict, data["lines"], elem_id_list)

    return note_bb_dict


def _build_note_output(
    source: str, page: str, note_elements_list: list[dict]
) -> list[dict]:
    """Generate the list of notes of a document

    Args:
       source: source of the document
       page: page of the document
       note_elements_list: list of note elements in a note

    Returns:
       the list of notes in a document with the right format

    """

    note_list = []

    for _elem_note_list in note_elements_list:
        text = "\n".join([_elem["text"] for _elem in _elem_note_list])
        elem_id_list = [_elem["orig"]["id"] for _elem in _elem_note_list]

        note_list.append(
            {"text": text, "source": source, "page": page, "elements": elem_id_list}
        )

    return note_list


def _extract_notes_from_datum(dat: dict, max_line_jumps: int) -> list[dict]:
    """Extract notes from one element

    Args:
      dat: dictionary with elements and lines property
      max_line_jumps: maximum number of jumps betwen note lines

    Returns:
      annotations with the note detections

    """


def _get_bboxes_of_lines(lines_id_list, lines, elements):
    coords_list = list()
    for line_id in lines_id_list:
        line = lines[line_id]
        elem_ids = [elem["id"] for elem in line["orig"]]
        elems_in_line = [_get_element_with_a_given_id(elements, id) for id in elem_ids]
        coords = merge_bbox_of_line(elems_in_line)
        coords_list.append(coords)
    return coords_list


def merge_bbox_of_line(elems_in_line):
    # to do tests
    cords_list = [elem["orig"] for elem in elems_in_line]
    bbox = {
        "x0": min([cords["x0"] for cords in cords_list]),
        "x1": max([cords["x1"] for cords in cords_list]),
        "y0": min([cords["y0"] for cords in cords_list]),
        "y1": max([cords["y1"] for cords in cords_list]),
    }
    return bbox


def _get_box_of_lines(id_lines, bbox_of_lines):

    box_list = dict()
    for id, line in enumerate(bbox_of_lines):
        line["text"] = ""
        box = Box(line)
        box_list[id_lines[id]] = box
    return box_list


def _get_element_with_a_given_id(elements, id) -> list[int]:
    """
    Returns the element which has the given ID
    Parameters
    ----------
    elements
    id:

    Returns element
    -------
    """
    for element in elements:
        if element["orig"]["id"] == id:
            return element


def _separate_notes_in_sentences(note_elements):
    new_elements = list()

    for note_group in note_elements:
        new_note_group = list()
        for note in note_group:
            text = note.get("text").replace("\n", "")

            if break_notes_before(text):
                if new_note_group:
                    new_elements.append(new_note_group)
                    new_note_group = list()

            new_note_group.append(note)

            if break_notes_after(text):
                new_elements.append(new_note_group)
                new_note_group = list()

        if new_note_group:
            new_elements.append(new_note_group)
            new_note_group = list()

    return new_elements


def break_notes_before(text):
    regex = r"^\s*[0-9]{1,2}\)|^\s*(-|\*)"  # enumerations starting by 1, 2), or with "-" or with "*"
    x = re.search(regex, text)
    if x:
        return True
    return False


def break_notes_after(text):
    if text.endswith(".") or text.endswith(". "):
        return True

    return False
