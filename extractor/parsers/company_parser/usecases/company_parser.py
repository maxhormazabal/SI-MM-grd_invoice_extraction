import copy
import logging

from extractor.common.usecases.base import BaseUseCase
from ..controllers.company_controller import CompanyParserController
from ..services.company_extractor import (
    extract_companies_from_element,
    get_company_of_body_tag,
    clean_company_name_in_subject_of_email,
)

logger = logging.getLogger("parser.company")


class CompanyParserUseCase(BaseUseCase):
    def __init__(self, input_data: dict):
        """Initialization of parameters

        Args:
          input_doc: dict with the parser input formats

        Result:
            result: a dict with original text and companies

        """

        super().__init__()
        self.input_data = copy.deepcopy(input_data)
        self.result = copy.deepcopy(input_data)

    def execute(self):
        """Parses the companies after they are tagged

        This parser generates annotations of type company that will be included in the output

        Leaves in result a Json with the same format as input with the result including the input and the parser annotations

        """

        try:
            input_data_copy = copy.deepcopy(self.input_data)
            controller = CompanyParserController(input_data_copy)
            result_annotations_list = []

            for idx, _datum in enumerate(input_data_copy["data"]):
                page = _datum["page"]
                source = _datum["source"]
                elements_with_companies_list = controller.process_input(_datum)
                for element in elements_with_companies_list:
                    element_id = element["orig"]["id"]
                    if element.get("body_client_tag"):
                        companies_found, element_id_list = get_company_of_body_tag(
                            element, _datum.get("elements")
                        )
                    elif input_data_copy.get("is_email_file"):
                        element = clean_company_name_in_subject_of_email(element)
                        companies_found = extract_companies_from_element(
                            element, use_orig=False
                        )
                    else:
                        companies_found = extract_companies_from_element(element)

                    element_id_list = [element_id]
                    for company in companies_found:
                        result_annotations_list.append(
                            {
                                "text": company,
                                "source": source,
                                "page": page,
                                "elements": element_id_list,
                                "body_client_tag": element.get(
                                    "body_client_tag", False
                                ),
                            }
                        )

            self.result = controller.process_result(result_annotations_list)
        except Exception as e:
            logger.error("{} - {}".format(e.__class__.__name__, e))
            logger.warning("Execution continues without company parsing")
            self.result = copy.deepcopy(self.input_data)
        return self.result
