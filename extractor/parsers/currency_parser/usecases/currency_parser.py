import copy
import logging

from extractor.common.usecases.base import BaseUseCase
from ..controllers.currency_controller import EmailParserController
from ..services.currency_extractor import find_currency
from ....common.cli.utils import read_json

logger = logging.getLogger("parser.currency")


class CurrencyParserUseCase(BaseUseCase):
    def __init__(self, input_data: dict, config: dict):
        """Initialization of parameters

        Args:
          input_doc: dict with the parser input formats

        Result:
            result: a dict with original text and currency

        """

        super().__init__()
        self.input_data = input_data
        self.config = config
        self.currency_alias = {}
        self.result = copy.deepcopy(input_data)

    def execute(self):
        """Parses the emails after they are tagged

        This parser generates annotations of type currency that will be included in the output

        Leaves in result a Json with the same format as input with the result including the input and the parser annotations

        """
        try:
            self.currency_alias = read_json(self.config["currency_config_file"])
            input_data_copy = copy.deepcopy(self.input_data)
            controller = EmailParserController(input_data_copy)
            currencies_found = []
            for idx, _datum in enumerate(input_data_copy["data"]):
                page = _datum["page"]
                source = _datum["source"]
                elements_with_currency_list = controller.process_input(_datum)
                for element in elements_with_currency_list:
                    element_id = element["orig"]["id"]
                    currencies = find_currency(
                        element["orig"]["text"], self.currency_alias
                    )
                    for currency in currencies:
                        currencies_found.append(
                            {
                                "text": currency[0],
                                "source": source,
                                "page": page,
                                "elements": [element_id],
                                "parser_currency_score": currency[1],
                            }
                        )

            self.result = controller.process_result(currencies_found)
        except Exception as e:
            logger.error("{} - {}".format(e.__class__.__name__, e))
            logger.warning("Execution continues without currency parsing")
            self.result = copy.deepcopy(self.input_data)
        return self.result
