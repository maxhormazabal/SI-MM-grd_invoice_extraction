import logging
import json
from .text_classifier_quant import QuantProcessor


logger = logging.getLogger("labeler.onnx")


def _get_samples_from_list(test_data_list, default_class):
    """List of samples to be converted

    Keyword arguments:
    test_data_list -- samples to be translated to bert format

    """
    sample_list = []

    for _test in test_data_list:

        logger.trace("_test {}".format(_test))

        json_object = json.loads(_test)
        # text = json_object["text"]
        # label is not relevant here
        # sample = [text, default_class]
        sample_list.append(json_object)

    return sample_list


def class_analyse(sample_list, extractor, trainer, default_class=None):
    """

    Keyword arguments:
    sample_list -- list of json objects with text/label
    extractor -- class extractor object
    trainer -- previosly trained model (already initialized)
    default_class (deprecated) -- class to assign in wrong samples

    """

    if default_class is not None:
        logger.warn("default_class is deprecated and will be removed in the future")

    test_list = _get_samples_from_list(sample_list, default_class)

    logger.trace("{}".format(test_list))

    result_class, confidence = extractor.predict(test_list, trainer)
    result_list = []

    for i in range(len(result_class)):
        _class = result_class[i]
        _conf = confidence[i]

        result_list.append(json.dumps({"label": _class, "confidence": str(_conf)}))

    return result_list


def class_initialization_quant(config):
    """Obtain a configuration file

    Keyword arguments:
    config -- configuration dict

    """

    extractor = QuantProcessor(config)

    trainer = extractor.init_model()

    return extractor, trainer
