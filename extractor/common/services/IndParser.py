import logging
from abc import ABC, abstractmethod
from extractor.common.services.Box import (
    Box,
    maximum_minimum_horizontal_or_vertical_distance_boxes,
    doHorizontalOverlap,
    doVerticalOverlap,
    vertical_distance_boxes,
    horizontal_distance_boxes,
)


class IndParser(ABC):
    def __init__(self):
        super().__init__()

    @staticmethod
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

    @staticmethod
    def get_score_element_based_on_distance(
        id_ind, annotation, elements, max_distance_score, ind_box
    ):

        """
        Calculates an score for an annotation of being a specific element.
        If it has an element in common with the indicator the score is 1. In any other case, the score
        is calculated considering the distance to the indicator.

        Parameters
        ----------
        id_ind: ID of the element labelled as a indicator
        annotation: possible annotations targeted by the indicator of interest
        elements: list of elements with a specific tag (same as annotation type)
        max_distance_score: Value of distance to normalize the score. Higher than this distance score is 0
        ind_box: Box object of the indicator element

        Returns the calculated score
        -------

        """
        # High value that will result in score 0 if not changed. Probably will be changed.
        INIT_INV_SCORE = 100

        if id_ind in annotation["elements"]:
            return 1, id_ind, None
        else:
            id_reference_element = None
            inv_score = INIT_INV_SCORE
            score_dimension = None
            for element_id in annotation["elements"]:
                element = IndParser._get_element_with_a_given_id(elements, element_id)
                element_box = Box(element["orig"])
                (
                    distance_sign,
                    distance_dimension,
                ) = maximum_minimum_horizontal_or_vertical_distance_boxes(
                    element_box, ind_box
                )
                distance = abs(distance_sign)

                new_score = distance / max_distance_score
                if new_score <= inv_score:
                    if not id_reference_element:
                        id_reference_element = element_id
                    if not score_dimension:
                        score_dimension = distance_dimension
                if new_score < inv_score:
                    inv_score = new_score
                    id_reference_element = element_id
                    score_dimension = distance_dimension
                # inv_score = new_score if new_score < inv_score else inv_score
            if inv_score > 1:
                inv_score = 1
            if inv_score < 0:
                inv_score = 0
            score = 1 - inv_score
            return score, id_reference_element, score_dimension

    @staticmethod
    def extract_labels_based_on_context(
        ind_tagged_elements: list[dict],
        annotations_with_a_given_tag: list[dict],
        elements_with_a_given_tag: list[dict],
        max_distance_score,
    ):
        """Extract annotations from element list of a page of a document

        Args:
          ind_tagged_elements: indicator elements
          annotations_with_a_given_tag: annotations
          elements_with_a_given_tag: elements with tag
          max_distance_score: Value of distance to normalize the score. Higher than this distance score is 0

        Returns:
          annotations with the detections and score
        """
        new_annotations = list()

        if len(ind_tagged_elements) == 0:
            for annotation in annotations_with_a_given_tag:
                annotation["score"] = 0.5
                annotation["position_info"] = {
                    "id_reference_ind": None,
                    "id_reference_element": None,
                }
                new_annotations.append(annotation)

        elif len(ind_tagged_elements) == 1:
            id_ind = ind_tagged_elements[0]["orig"]["id"]
            ind_box = Box(ind_tagged_elements[0]["orig"])
            for annotation in annotations_with_a_given_tag:
                (
                    annotation["score"],
                    id_reference_element,
                    score_dimension,
                ) = IndParser.get_score_element_based_on_distance(
                    id_ind,
                    annotation,
                    elements_with_a_given_tag,
                    max_distance_score,
                    ind_box,
                )
                annotation["position_info"] = {
                    "id_reference_ind": id_ind,
                    "id_reference_element": id_reference_element,
                    "score_dimension": score_dimension,
                }
                if ind_tagged_elements[0].get("body_client_tag"):
                    annotation["body_client_tag"] = True
                new_annotations.append(annotation)
        else:
            for annotation in annotations_with_a_given_tag:
                annotation["score"] = 0
                annotation["position_info"] = {
                    "id_reference_ind": ind_tagged_elements[0]["orig"]["id"],
                    "id_reference_element": annotation["elements"][0],
                    "score_dimension": None,
                }
                for ind_elem in ind_tagged_elements:
                    ind_box = Box(ind_elem["orig"])
                    id_ind = ind_elem["orig"]["id"]
                    (
                        new_score,
                        id_reference_element,
                        score_dimension,
                    ) = IndParser.get_score_element_based_on_distance(
                        id_ind,
                        annotation,
                        elements_with_a_given_tag,
                        max_distance_score,
                        ind_box,
                    )
                    if new_score > annotation["score"]:
                        annotation["score"] = new_score
                        annotation["position_info"] = {
                            "id_reference_ind": id_ind,
                            "id_reference_element": id_reference_element,
                            "score_dimension": score_dimension,
                        }
                new_annotations.append(annotation)
        return new_annotations

    @staticmethod
    def extract_position_element(
        ind_tagged_elements: list[dict],
        annotations: list[dict],
        elements_with_a_given_tag: list[dict],
    ):

        if len(ind_tagged_elements) == 0:
            for annotation in annotations:
                annotation["position_info"].update(
                    {"h_overlap": None, "v_overlap": None}
                )
            return annotations

        id_to_elem = dict()
        for elem_ind in ind_tagged_elements:
            id_to_elem[elem_ind["orig"]["id"]] = elem_ind

        for i, annotation in enumerate(annotations):
            id_ind_element = annotation["position_info"]["id_reference_ind"]
            ind_box = Box((id_to_elem[id_ind_element])["orig"])

            element_box = Box(
                IndParser._get_element_with_a_given_id(
                    elements_with_a_given_tag,
                    annotation["position_info"]["id_reference_element"],
                )["orig"]
            )

            v_overlap, h_overlap = IndParser.check_overlapping(ind_box, element_box)
            annotation["position_info"].update(
                {"h_overlap": h_overlap, "v_overlap": v_overlap}
            )
        return annotations

    @staticmethod
    def check_overlapping(ind_box, element_box):
        if doVerticalOverlap(ind_box, element_box):
            v_overlap = "overlap"
        else:
            v_overlap = (
                "above"
                if vertical_distance_boxes(ind_box, element_box) > 0
                else "below"
            )

        if doHorizontalOverlap(ind_box, element_box):
            h_overlap = "overlap"
        else:
            h_overlap = (
                "right"
                if horizontal_distance_boxes(ind_box, element_box) > 0
                else "left"
            )

        return v_overlap, h_overlap
