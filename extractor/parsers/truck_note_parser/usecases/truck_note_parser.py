import copy
import logging

from extractor.common.usecases.base import BaseUseCase
from ..controllers.truck_note_controller import TruckNoteController
from ..services.truck_note_extractor import get_truck_note_using_notes

logger = logging.getLogger("parser.truck_note")


class TruckNoteParserUseCase(BaseUseCase):
    def __init__(self, input_data: dict):
        """Initialization of parameters

        Args:
          config: dict with configuration
          input_data: dict with the parser input format

        """

        super().__init__()
        self.input_data = input_data
        self.result = None

    def execute(self):
        """Parses the truck notes after they are tagged

        This parser generates annotations of type truck_note that will be included in the output

        Leaves in result a Json with the same format as input with the result including the input and the parser annotations

        """
        try:
            input_data_copy = copy.deepcopy(self.input_data)
            controller = TruckNoteController(input_data_copy)

            result_annotations_list = []
            for idx, _datum in enumerate(input_data_copy["data"]):
                page = _datum["page"]
                source = _datum["source"]
                notes_annotations = controller.get_parsed_notes(input_data_copy, page)
                truck_notes_elements = controller.process_input(_datum)
                already_used_elements = []
                for element in truck_notes_elements:
                    if element["orig"]["id"] not in already_used_elements:
                        text, elements = get_truck_note_using_notes(
                            element, notes_annotations
                        )
                        already_used_elements += elements
                        result_annotations_list.append(
                            {
                                "text": text,
                                "source": source,
                                "page": page,
                                "elements": elements,
                            }
                        )

            self.result = controller.process_result(result_annotations_list)
        except Exception as e:
            logger.error("{} - {}".format(e.__class__.__name__, e))
            logger.warning("Execution continues without truck_note parsing")
            self.result = copy.deepcopy(self.input_data)
        return self.result
