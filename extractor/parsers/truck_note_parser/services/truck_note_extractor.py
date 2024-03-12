import logging
import copy
from extractor.common.services.Box import Box, vertical_distance_boxes

logger = logging.getLogger("parser.truck_note")


def get_whole_note_using_truck_note(truck_note, note_annotations):

    id_truck_note = truck_note["orig"]["id"]
    text = truck_note["text"]
    elements = [id_truck_note]

    for note in note_annotations:
        if id_truck_note in note["elements"]:
            text = note["text"]
            elements = note["elements"]

    return text, elements


def get_truck_note_using_notes(truck_note, note_annotations):

    id_truck_note = truck_note["orig"]["id"]
    text = truck_note["text"]
    elements = [id_truck_note]

    for note in note_annotations:
        if id_truck_note in note["elements"]:
            text = note["text"].replace("\n", " ").strip()
            elements = note["elements"]
            if len(elements) > 3:
                elements = get_elements_coappearing(id_truck_note, elements)

    return text, elements


def get_elements_coappearing(id_truck_note, elements):
    """

    Parameters
    ----------
    id_truck_note - id of truck note
    elements - list of ids in a note

    Returns the element of the truck id together with the previous and following one in the list of elements
    -------

    """
    if len(elements) == 0:
        return []
    if len(elements) == 1:
        return [id_truck_note]
    if id_truck_note == elements[0]:
        return elements[:2]
    if id_truck_note == elements[-1]:
        return elements[-2:]
    try:
        index = elements.index(id_truck_note)
        return elements[index - 1 : index + 2]
    except Exception:
        return []
