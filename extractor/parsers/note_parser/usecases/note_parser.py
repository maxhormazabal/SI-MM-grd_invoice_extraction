import os
import sys
import copy
import logging
from ..services.custom_exceptions import NoteParserError

from extractor.common.usecases.base import BaseUseCase
from ..services.note_extractor import (
    _separate_notes_in_sentences,
    _detect_note_boundingboxes,
    _get_note_elements_in_bb,
    _build_note_output,
)

logger = logging.getLogger("parser.note")


class NoteParserUseCase(BaseUseCase):
    def __init__(self, config: dict, input_doc: dict):
        """Initialization of parameters

        Args:
          config: dict with configuration
          input_doc: dict with the parser input format

        """

        super().__init__()
        self.config = config
        self.input_doc = input_doc
        self.result = None

    def execute(self):
        """Parses the notes after they are tagged

        This parser generates annotations of type note that will be included in the output

        Leaves in result a Json with the same format as input with the result including the input and the parser annotations

        """
        try:
            max_line_jumps = self.config.get("max_line_jumps")

            """Extract note annotations

            Args:
              input_doc: document with input document
              max_line_jumps: maximum number of jumps betwen note lines

            Returns:
              the input dict including the note annotations

            """

            result_doc = copy.deepcopy(self.input_doc)

            result_doc.get("annotations", {})
            result_doc["annotations"]["note"] = []

            for _datum in self.input_doc.get("data"):
                if "elements" not in _datum or "lines" not in _datum:
                    raise NoteParserError(
                        "Every document should contain lines and elements"
                    )

                note_bb_dict = _detect_note_boundingboxes(_datum, max_line_jumps)

                # Get note elements
                note_elements_list = _get_note_elements_in_bb(
                    note_bb_dict, _datum.get("elements")
                )

                note_elements_list = _separate_notes_in_sentences(note_elements_list)

                note_list = _build_note_output(
                    _datum.get("source"), _datum.get("page"), note_elements_list
                )

                if len(note_list) > 0:
                    result_doc["annotations"]["note"] += note_list

            self.result = result_doc

        except Exception as e:
            logger.error("{} - {}".format(e.__class__.__name__, e))
            logger.warning("Execution continues without note parsing")
            self.result = copy.deepcopy(self.input_doc)
        return self.result
