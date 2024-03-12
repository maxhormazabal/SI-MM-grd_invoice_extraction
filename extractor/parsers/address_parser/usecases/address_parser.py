import copy
import logging

from extractor.ocr_utils import is_hybrid_order
# sys.path.append(os.path.abspath("..."))
from extractor.common.usecases.base import BaseUseCase
from ..controllers.AddressController import AddressParserController
from ..services.address_extractor import (
    _get_parsed_elements,
    get_address_from_elements,
    _build_address_output,
    filter_email_inds
)

logger = logging.getLogger("parser.address")


class AddressParserUseCase(BaseUseCase):
    def __init__(self, config: dict, input_data: dict):
        """Initialization of parameters

        Args:
          config: dict with configuration
          input_doc: dict with the parser input format

        """

        super().__init__()
        self.config = config
        self.input_data = input_data
        self.result = self.input_data

    def execute(self):
        """Parses the address after they are tagged

        This parser generates annotations of type note that will be included in the output

        Leaves in result a Json with the same format as input with the result including the input and the parser annotations

        """
        try:
            input_data_copy = copy.deepcopy(self.input_data)
            address_controller = AddressParserController(input_data_copy)
            result_annotations_list = []

            for idx, _datum in enumerate(self.result["data"]):
                page = _datum["page"]
                source = _datum["source"]

                is_last_page = (idx == len(self.result["data"])-1)
                elements_with_address_list = address_controller.process_input(_datum, is_last_page)
                parsed_elements = _get_parsed_elements(
                    elements_with_address_list, self.config["max_words_address"]
                )

                (
                    preannotations_unique,
                    preannotations_groups,
                ) = get_address_from_elements(
                    parsed_elements,
                    self.config["max_words_considered_unique_address"],
                    self.config["max_line_jumps"],
                    self.config["max_horizontal_distance_elements"],
                )

                annotations_page = _build_address_output(
                    preannotations_unique, preannotations_groups, source, page
                )

                if _datum.get("is_email_file") or is_hybrid_order(_datum):
                    annotations_page = filter_email_inds(annotations_page)

                result_annotations_list += annotations_page

            self.result = address_controller.process_result(
                result_annotations_list, self.result
            )
        except Exception as e:
            logger.error("{} - {}".format(e.__class__.__name__, e))
            logger.warning("Execution continues without address parsing")
            self.result = copy.deepcopy(self.input_data)
        return self.result
