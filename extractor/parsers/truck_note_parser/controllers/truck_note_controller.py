import copy
from abc import ABC

from extractor.common.controllers.base import BaseController
from extractor.parsers.truck_note_parser.controllers.custom_exceptions import (
    TruckNoteParserError,
)


class TruckNoteController(BaseController, ABC):
    def __init__(self, input_data: dict):
        """Initialization of parameters

        Args:
          input_data: dict with the parser input formats

        """

        super().__init__()
        self.input_data = input_data
        self.result_doc = copy.deepcopy(input_data)

    def process_input(self, data: dict) -> list[str]:

        if "elements" not in data or "lines" not in data:
            raise TruckNoteParserError(
                "Every document should contain lines and elements"
            )

        lines_list = self.get_elements_with_a_given_tag(data["elements"], "TRUCK_NOTE")
        return lines_list

    def process_result(self, truck_elements: list[dict]) -> list[dict]:

        if "annotations" not in self.result_doc:
            self.result_doc["annotations"] = {}
        if "truck_note" not in self.result_doc["annotations"]:
            self.result_doc["annotations"]["truck_note"] = []

        if len(truck_elements) > 0:
            self.result_doc["annotations"]["truck_note"] += truck_elements
        return self.result_doc

    def get_parsed_notes(self, input_data, page):

        if "annotations" not in input_data:
            raise TruckNoteParserError(
                "Note parser should be run before truck note parser"
            )
        if "note" not in input_data["annotations"]:
            raise TruckNoteParserError(
                "Note parser should be run before truck note parser"
            )

        notes = input_data["annotations"]["note"]
        notes = [note for note in notes if note["page"] == page]
        return notes
