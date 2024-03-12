import copy
import logging

from extractor.common.usecases.base import BaseUseCase
from ..controllers.person_controller import PersonParserController
from ..services.person_extractor import extract_person_name_from_string

logger = logging.getLogger("parser.person")


class PersonParserUseCase(BaseUseCase):
    def __init__(self, input_data: dict):
        """Initialization of parameters

        Args:
          input_doc: dict with the parser input formats

        Result:
            result: a dict with original text and person names

        """

        super().__init__()
        self.input_data = input_data
        self.result = copy.deepcopy(input_data)

    def execute(self):
        """Parses names of persons after they are tagged

        This parser generates annotations of type person that will be included in the output

        Leaves in result a Json with the same format as input with the result including the input and the parser annotations

        """
        try:
            input_data_copy = copy.deepcopy(self.input_data)
            person_controller = PersonParserController(input_data_copy)
            result_annotations_list = []

            for idx, _datum in enumerate(input_data_copy["data"]):
                page = _datum["page"]
                source = _datum["source"]
                elements_with_persons_list = person_controller.process_input(_datum)
                for element in elements_with_persons_list:
                    element_id = element["orig"]["id"]
                    persons_found = extract_person_name_from_string(
                        element["orig"]["text"].rstrip("\n")
                    )

                    if persons_found:
                        for person in persons_found:
                            result_annotations_list.append(
                                {
                                    "text": person,
                                    "source": source,
                                    "page": page,
                                    "elements": [element_id],
                                }
                            )

            self.result = person_controller.process_result(result_annotations_list)
        except Exception as e:
            logger.error("{} - {}".format(e.__class__.__name__, e))
            logger.warning("Execution continues without person parsing")
            self.result = copy.deepcopy(self.input_data)
        return self.result
