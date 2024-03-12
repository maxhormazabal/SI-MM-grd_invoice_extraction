import copy
import logging

from extractor.common.usecases.base import BaseUseCase
from ..controllers.CIF_controller import CIFController
from ..services.CIF_services import (
    clean_element,
    extract_cif_from_element,
    has_cif_word,
    get_cif_from_line,
)

logger = logging.getLogger("parser.CIF")


class CIFParserUseCase(BaseUseCase):
    def __init__(self, config: dict, input_data: dict):
        """Initialization of parameters

        Args:
          config
          input_doc: dict with the parser input formats

        Result:
            result: a dict with original text and CIF

        """

        super().__init__()
        self.config = config
        self.cif_indicators = self.config["cif_indicators"]
        self.input_data = input_data
        self.result = copy.deepcopy(input_data)

    def execute(self):
        """Parses the CIFs

        This parser generates annotations of type date that will be included in the output

        Leaves in result a Json with the same format as input with the result including the input and the CIF annotations

        """
        try:
            input_data_copy = copy.deepcopy(self.input_data)
            cif_controller = CIFController(input_data_copy)
            result_annotations_list = []

            for idx, _datum in enumerate(input_data_copy["data"]):
                page = _datum["page"]
                source = _datum["source"]
                elements = cif_controller.process_input(_datum)

                for element in elements:
                    element_id = element["orig"]["id"]
                    original_element_text = element["orig"]["text"].replace("\n", "")
                    element_text = original_element_text
                    element_text_lower = element_text.lower()
                    contains_keyword = False

                    if has_cif_word(element_text_lower, self.cif_indicators) or (
                        "ORDERID" in element.get("labels")
                        and len(element.get("text").replace("\n", "")) > 5
                    ):
                        not_cleaned_element_text = element_text
                        element_text = clean_element(element_text)
                        contains_keyword = True

                    cif, related_company = extract_cif_from_element(element_text)

                    if cif:
                        result_annotations_list.append(
                            cif_controller.format_cif_annotation(
                                cif,
                                source,
                                page,
                                [element_id],
                                related_company,
                                original_element_text,
                            )
                        )
                    elif contains_keyword:
                        text = None
                        if len(element_text.split()) == 1:
                            text = element_text
                        else:
                            text = get_cif_from_line(
                                not_cleaned_element_text, self.cif_indicators
                            )

                        if text:
                            result_annotations_list.append(
                                cif_controller.format_cif_annotation(
                                    text,
                                    source,
                                    page,
                                    [element_id],
                                    None,
                                    element_text,
                                )
                            )

            self.result = cif_controller.process_result(result_annotations_list)
        except Exception as e:
            logger.error("{} - {}".format(e.__class__.__name__, e))
            logger.warning("Execution continues without CIF parsing")
            self.result = copy.deepcopy(self.input_data)
        return self.result
