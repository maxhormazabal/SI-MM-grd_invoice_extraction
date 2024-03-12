import copy
import logging
import traceback

from extractor.common.usecases.base import BaseUseCase
from extractor.common.services.IndParser import IndParser
from ..controllers.date_controller import DateParserController
from ..services.date_extractor import extract_dates_from_string

logger = logging.getLogger("parser.date")


class DateParserUseCase(BaseUseCase):
    def __init__(self, input_data: dict, config: dict):
        """Initialization of parameters

        Args:
          input_doc: dict with the parser input formats

        Result:
            result: a dict with original text and dates

        """

        super().__init__()
        self.input_data = input_data
        self.result = input_data
        self.config = config

    def execute(self):
        """Parses the dates after they are tagged

        This parser generates annotations of type date that will be included in the output

        Leaves in result a Json with the same format as input with the result including the input and the parser annotations

        """
        try:
            input_data_copy = self.input_data
            date_controller = DateParserController(input_data_copy)
            result_annotations_list = []
            result_annotation_hour_list = []
            result_annotations_list_final = []

            for idx, _datum in enumerate(input_data_copy["data"]):
                page = _datum["page"]
                source = _datum["source"]
                elements_with_dates_list = date_controller.process_input(_datum)
                elements_with_hours_list = (
                    date_controller.get_elements_with_a_given_tag(
                        _datum["elements"], "HOUR"
                    )
                )
                result_annotations_list = []
                result_annotation_hour_list = []
                for element in elements_with_dates_list:
                    if ("NOTE" not in element["labels"]) or (
                        "NOTE" in element["labels"]
                        and "DATEIND" in element["labels"]
                        and "DATE" in element["labels"]
                    ):
                        element_id = element["orig"]["id"]
                        date_found, sucessfully_parsed = extract_dates_from_string(
                            element["orig"]["text"].rstrip("\n")
                        )
                        if date_found:
                            result_annotations_list.append(
                                {
                                    "text": date_found,
                                    "source": source,
                                    "page": page,
                                    "elements": [element_id],
                                    "sucessfully_parsed": sucessfully_parsed,
                                    "email_ind_tagged": element.get("body_date_tag"),
                                }
                            )

                [
                    result_annotation_hour_list.append(
                        {
                            "text": element.get("text"),
                            "source": source,
                            "page": page,
                            "elements": [element["orig"]["id"]],
                            "score": 1.0,
                        }
                    )
                    for element in elements_with_hours_list
                ]

                # dates ind tagged
                datesind_tagged = date_controller.get_elements_with_a_given_tag(
                    _datum["elements"], "DATEIND"
                )
                if _datum.get("is_email_file", False):
                    if any(
                        [date.get("body_date_tag", False) for date in datesind_tagged]
                    ):
                        datesind_tagged = [
                            date
                            for date in datesind_tagged
                            if date.get("body_date_tag", False)
                        ]

                date_elements = date_controller.get_elements_with_a_given_tag(
                    _datum["elements"], "DATE"
                )

                if len(date_elements) > 0:
                    result_annotations_list = IndParser.extract_labels_based_on_context(
                        datesind_tagged,
                        result_annotations_list,
                        date_elements,
                        self.config["max_distance_score"],
                    )
                    result_annotations_list_final += IndParser.extract_position_element(
                        datesind_tagged, result_annotations_list, date_elements
                    )

            self.result = date_controller.process_result(
                result_annotations_list_final, "date"
            )
            self.result = date_controller.process_result(
                result_annotation_hour_list, "hour"
            )

        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error("{} - {}".format(e.__class__.__name__, e))
            logger.warning("Execution continues without date parsing")
            self.result = copy.deepcopy(self.input_data)

        return self.result
