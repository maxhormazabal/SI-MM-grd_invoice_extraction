import copy
import logging
import traceback

from extractor.common.services.IndParser import IndParser
from extractor.common.usecases.base import BaseUseCase
from ..controllers.payment_controller import PaymentParserController

logger = logging.getLogger("parser.payment")


class PaymentParserUseCase(BaseUseCase):
    def __init__(self, config: dict, input_data: dict):
        """Initialization of parameters

        Args:
          input_doc: dict with the parser input formats

        Result:
            result: a dict with original text and payment note ids

        """

        super().__init__()
        self.config = config
        self.input_data = input_data
        self.result = copy.deepcopy(input_data)

    def execute(self):
        """Parses the  payment note ids after they are tagged

        This parser generates annotations of type  payment ote that will be included in the output

        Leaves in result a Json with the same format as input with the result including the input and the parser annotations

        """
        try:
            input_data_copy = copy.deepcopy(self.input_data)
            payment_controller = PaymentParserController(input_data_copy)
            payment_controller.process_input()

            for idx, _datum in enumerate(input_data_copy["data"]):
                page = _datum["page"]
                source = _datum["source"]

                payind_tagged = payment_controller.get_elements_with_a_given_tag(
                    _datum["elements"], "PAYMENT_IND"
                )
                paynote_elements = payment_controller.get_elements_with_a_given_tag(
                    _datum["elements"], "PAYMENT_NOTE"
                )

                payment_note_annotations = (
                    payment_controller.transform_element_to_annotation(
                        paynote_elements, page, source
                    )
                )

                payment_note_list = IndParser.extract_labels_based_on_context(
                    payind_tagged,
                    payment_note_annotations,
                    paynote_elements,
                    self.config["max_distance_score"],
                )

                if not payind_tagged:
                    for note in payment_note_list:
                        note["score"] = 1

                paymentid_list = IndParser.extract_position_element(
                    payind_tagged, payment_note_list, paynote_elements
                )

                self.result = payment_controller.process_result(paymentid_list)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error("{} - {}".format(e.__class__.__name__, e))
            logger.warning("Execution continues without payment note parsing")
            self.result = copy.deepcopy(self.input_data)
        return self.result
