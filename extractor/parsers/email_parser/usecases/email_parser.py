import copy
import logging

from extractor.common.usecases.base import BaseUseCase
from ..controllers.parser_controller import EmailParserController
from ..services.email_extractor import find_email_text, find_emails_with_ocr_errors

logger = logging.getLogger("parser.email")


class EmailParserUseCase(BaseUseCase):
    def __init__(self, input_data: dict, config: dict):
        """Initialization of parameters

        Args:
          input_doc: dict with the parser input formats

        Result:
            result: a dict with original text and emails

        """

        super().__init__()
        self.input_data = input_data
        self.result = copy.deepcopy(input_data)
        self.config = config

    def execute(self):
        """Parses the emails after they are tagged

        This parser generates annotations of type email that will be included in the output

        Leaves in result a Json with the same format as input with the result including the input and the parser annotations

        """
        try:
            input_data_copy = copy.deepcopy(self.input_data)
            controller = EmailParserController(input_data_copy)
            result_annotations_list = []

            for idx, _datum in enumerate(input_data_copy["data"]):
                page = _datum["page"]
                source = _datum["source"]
                elements_with_email_list = controller.process_input(_datum)
                emails_found = []
                for element in elements_with_email_list:
                    element_id = element["orig"]["id"]
                    emails_found = find_email_text(element.get("text").rstrip("\n"))
                    for email in emails_found:
                        result_annotations_list.append(
                            {
                                "text": email,
                                "source": source,
                                "page": page,
                                "elements": [element_id],
                            }
                        )
                if not emails_found:
                    corrected_elements_with_email_list = find_emails_with_ocr_errors(
                        _datum.get("elements"),
                        elements_with_email_list,
                        self.config.get("email_domains"),
                        self.config.get("symbols_replace_at_in_ocr_errors"),
                    )
                    for element in corrected_elements_with_email_list:
                        element_id = element["orig"]["id"]
                        emails_found = find_email_text(element.get("text").rstrip("\n"))
                        for email in emails_found:
                            result_annotations_list.append(
                                {
                                    "text": email,
                                    "source": source,
                                    "page": page,
                                    "elements": [element_id],
                                }
                            )

            self.result = controller.process_result(result_annotations_list)
        except Exception as e:
            import traceback

            logger.debug(traceback.format_exc())
            logger.error("{} - {}".format(e.__class__.__name__, e))
            logger.warning("Execution continues without email parsing")
            self.result = copy.deepcopy(self.input_data)
        return self.result
