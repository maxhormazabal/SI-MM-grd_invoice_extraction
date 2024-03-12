import logging
import json
from .onnxinference.text_classifier_wrapper import (
    class_initialization_quant,
    class_analyse,
)
from .custom_exceptions import TagDocumentError

logger = logging.getLogger("labeler.onnx")


def _tag_elements(config: dict, input_doc: dict):
    """Annotate elements with labels

    Args:
        config: dictionary with the configuration of the parser
        input_doc: input file

    """

    # fake service
    extractor, trainer = class_initialization_quant(config["multi"])

    # build label dict
    label_dict = {}
    for idx, _label in enumerate(config["multi"]["label_list"]):
        label_dict[_label] = idx

    for _datum in input_doc["data"]:
        if "elements" not in _datum or "lines" not in _datum:
            raise TagDocumentError("Every document should contain lines and elements")

        for _elem in _datum["elements"]:
            sample_list = [json.dumps({"text": _elem["text"]})]

            # obtain a list of json with label, confidence properties
            result = class_analyse(sample_list, extractor, trainer)[0]

            result = json.loads(result)
            labels = result["label"]["labels"]

            confidence_list = []

            for _label in labels:
                confidence_list.append(result["label"]["preds"][label_dict[_label]])

            _elem["labels"] = labels
            _elem["confidence"] = confidence_list

    del trainer["model"]


def _tag_lines(config: dict, input_doc: dict):
    """Annotate lines with label

    Args:
       config: dictionary with the configuration of the parser
       input_doc: input_file

    """

    extractor, trainer = class_initialization_quant(config["single"])

    for _datum in input_doc["data"]:
        if "elements" not in _datum or "lines" not in _datum:
            raise TagDocumentError("Every document should contain lines and elements")

        for _lines in _datum["lines"]:
            sample_list = [json.dumps({"text": _lines["text"]})]

            # obtain a list of json with label, confidence properties
            result = class_analyse(sample_list, extractor, trainer)[0]
            result = json.loads(result)

            if result["label"] == "NOCLASS":
                pass

            else:
                label = result["label"]
                confidence = result["confidence"]

                _lines["labels"] = [label]
                _lines["confidence"] = [confidence]

    del trainer["model"]


def tag_elements(config: dict, input_doc: dict):
    """Annotate elements with labels

    Args:
        config: dictionary with the configuration of the parser
        input_doc: input file

    """
    _tag_elements(config, input_doc)
    _tag_lines(config, input_doc)

    return input_doc
