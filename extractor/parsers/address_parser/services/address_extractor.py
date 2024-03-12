import re
import logging
import pyap
from extractor.common.services.Box import (
    Box,
    boxes_same_column,
    vertical_distance_boxes,
    boxes_same_line,
    horizontal_distance_boxes,
)

logger = logging.getLogger("parser.address")


ADDRESS_TAGS = ["ADDRESS1", "ADDRESSX"]


def _get_parsed_elements(
    element_list: list[dict], max_words_address: int
) -> list[dict]:
    """

    Parameters
    ----------
    element_list: list of elements labelled as address
    max_words_address: maximum words in an address tagged element for not being parsed

    Returns the list received with the elements completed with the parsed address, with the size of words of that parsed address and with
    a boolean value indicating if the parsed address has been cropped from the original text or if it is just the original text
    -------

    """
    for addr_element in element_list:
        text_splitted = addr_element["text"].split()
        addr_element["len_words"] = len(
            text_splitted
        )  # to do: not count symbols like " - "
        if (len(addr_element["labels"]) == 1) and (
            len(text_splitted) <= max_words_address
        ):
            addr_element["parsed_address"] = addr_element["text"]
            addr_element["cropped"] = False
        elif len(addr_element["labels"]) == 1:
            addr_element["parsed_address"] = addr_element["text"]
            addr_element["cropped"] = True
        else:  # do something different
            address_elements, worked = parse_english_address_pyap(addr_element["text"])
            if not worked:
                address_elements = addr_element["text"]
            addr_element["parsed_address"] = address_elements
            addr_element["cropped"] = True

    return element_list


def parse_english_address_pyap(text):
    """
    Parses the text looking for addresses using the Pyap library.
    Parameters
    ----------
    text

    Returns:
    addresses: String with the text parsed
    boolean value: True if the parsing obtained any elements, false if it didnt work and didn't find any address
    -------

    """

    addresses = pyap.parse(text, country="GB")
    if len(addresses) == 0:
        return "", False
    addresses = ", ".join([str(x) for x in addresses])
    return addresses, True


def get_address_from_elements(
    parsed_elements: list[dict],
    max_words_considered_unique_address: int,
    max_line_jumps: int,
    max_horizontal_distance_elements: int,
) -> list[dict]:
    """

    Parameters
    ----------
    parsed_elements: list of parsed address
    max_words_considered_unique_address: If an address text has more than this number of words, is considered a full address and will not be joined with others
    max_line_jumps: maximum number of jumps between address lines
    max_horizontal_distance_elements: Max distance in pixels to consider two address elements of the same line being part of the same address
    Returns
    preannotations_unique: dictionary whose values are lists of 1 address element
    preannotations_groups: dictionary whose values are lists. Each list is a group of addresses elements that are together in the document
    -------

    """

    preannotations_unique = dict()
    preannotations_groups = dict()
    id_annotation = 0
    for element in parsed_elements:
        if element["len_words"] >= max_words_considered_unique_address:
            preannotations_unique[id_annotation] = [element]
            id_annotation += 1
        else:
            if len(preannotations_groups) == 0:
                preannotations_groups[id_annotation] = [element]

                id_annotation += 1
            else:
                current_preannotations_groups = preannotations_groups.copy()
                for (
                    anots_id
                ) in (
                    current_preannotations_groups
                ):  # buscar en cada conjunto de elementos
                    box_candidate = Box(element["orig"])
                    for el in current_preannotations_groups[
                        anots_id
                    ]:  # por cada elemento comprobar
                        is_break = False
                        box_reference = Box(el["orig"])

                        if box_below_or_netxto_another(
                            box_candidate,
                            box_reference,
                            max_horizontal_distance_elements,
                            max_line_jumps,
                        ):
                            preannotations_groups[anots_id] = preannotations_groups[
                                anots_id
                            ] + [element]
                            is_break = True
                            break
                    if is_break:
                        break
                else:
                    preannotations_groups[id_annotation] = [element]
                    id_annotation += 1

    return preannotations_unique, preannotations_groups


def box_below_or_netxto_another(
    box1, box2, max_horizontal_distance_elements, max_line_jumps
):
    """
    Parameters
    ----------
    box1
    box2
    max_horizontal_distance_elements: Max distance in pixels to consider two address elements of the same line being part of the same address
    max_line_jumps:  maximum number of jumps between address lines

    Returns
    -------

    """
    if is_nextto_annotation(box1, box2, max_horizontal_distance_elements):
        return True
    elif is_below_annotation(box1, box2, max_line_jumps):
        return True
    else:
        return False


def _build_address_output(
    preannotations_unique: list[dict],
    preannotations_groups: list[dict],
    source: str,
    page: str,
) -> list[dict]:
    """Generate the list of address of a document

    Args:
       source: source of the document
       page: page of the document
       note_elements_list: list of address elements in a note

    Returns:
       the list of address in a document with the right format

    """

    annotations = list()
    for preanot_id in preannotations_unique:
        preanot = preannotations_unique[preanot_id][0]
        anot = {
            "text": preanot["parsed_address"],
            "source": source,
            "page": page,
            "elements": [preanot["orig"]["id"]],
        }
        annotations.append(anot)

    for address_group in preannotations_groups.values():
        address = ", ".join([x["parsed_address"] for x in address_group])
        address_ids = [x["orig"]["id"] for x in address_group]
        anot = {
            "text": address,
            "source": source,
            "page": page,
            "elements": address_ids,
        }
        annotations.append(anot)

    return annotations


def is_nextto_annotation(
    box_candidate: Box, box_reference: Box, max_horizontal_distance_elements: int
):
    if boxes_same_line(box_candidate, box_reference):
        hdist = horizontal_distance_boxes(
            box_candidate, box_reference, scope="center", abs_value=True
        )
        if abs(hdist) < max_horizontal_distance_elements:
            return True
    return False


def is_below_annotation(box_candidate: Box, box_reference: Box, max_line_jumps: int):
    """
    Checks if the two given boxes are in the same column and above/below each other
    Parameters
    ----------
    box_candidate: Box object of the candidate element
    box_reference: Box object of the reference element
    max_line_jumps: maximum number of jumps between address lines

    Returns True if the candidate box is just below or just above the reference box
    -------

    """
    if boxes_same_column(box_candidate, box_reference, threshold=25):
        vdist = vertical_distance_boxes(
            box_candidate, box_reference, abs_value=True, scope="center"
        )
        if (
            abs(vdist) < box_candidate.height * 1.25 * max_line_jumps
        ):  # X lineas de separación, mas un 0.25 de margen de interlineado
            return True
    return False


def filter_email_inds(annotations):

    filtered_annotations = []
    regex_find_only_dir = r"(?i)(?:.*)(#dir.*)"
    for annotation in annotations:
        if "#dir" in annotation.get("text").lower():
            match = re.findall(regex_find_only_dir, annotation.get("text"))
            annotation["text"] = match[0]
        filtered_annotations.append(annotation)

    return filtered_annotations
