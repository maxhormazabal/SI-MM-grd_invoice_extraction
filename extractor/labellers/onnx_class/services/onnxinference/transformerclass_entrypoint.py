import logging
import json
import yaml
from .text_classifier_wrapper import class_initialization_quant, class_analyse

logger = logging.getLogger("labeler.onnx")


def test_samples_from_file(_file):
    """Obtain test samples from a file

    Only reads the line of the file without any processing

    Keyword arguments:
    _file: input file with testing samples

    """

    sample_list = []
    with open(_file, "r") as f_in:
        for line in f_in:
            line = line.rstrip("\n")
            sample_list.append(line)

    return sample_list


def analyse(test_file, config_file):
    """

    Keyword arguments
    test_file -- a file with json samples with text property
    config_file -- a configuration file


    """

    config = None
    with open(config_file, "r") as f_stream:
        config = yaml.load(f_stream, Loader=yaml.FullLoader)

    extractor, trainer = class_initialization_quant(config)

    # obtain a list of json objects with text/label properties
    sample_list = test_samples_from_file(test_file)

    # obtain a list of json with label, confidence properties
    result_list = class_analyse(sample_list, extractor, trainer)

    del trainer["model"]

    # only showing results on logging
    for _res in result_list:
        logger.trace("RESULT {}".format(_res))
