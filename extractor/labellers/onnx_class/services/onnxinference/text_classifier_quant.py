import numpy as np
import logging
import os
import onnxruntime
from scipy.special import softmax
from transformers import AutoTokenizer, BatchEncoding, TensorType
from .custom_exceptions import (
    ModelExecutionError,
    TokenizerError,
    ModelInitializationError,
)


logger = logging.getLogger("labeler.onnx")


class QuantProcessor(object):
    """Class to train and eval BERT classifier models"""

    def init_model(self):
        """Obtain a trainer to be used later for prediction"""

        try:

            tokenizer = AutoTokenizer.from_pretrained(self.config["tokenizer_name"])

            sess_options = onnxruntime.SessionOptions()
            sess_options.graph_optimization_level = (
                onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
            )
            sess_options.intra_op_num_threads = 1
            session = onnxruntime.InferenceSession(
                self.config["model_name_or_path"], sess_options, providers=['AzureExecutionProvider', 'CPUExecutionProvider']
            )

            trainer = {"model": session, "tokenizer": tokenizer}

        except Exception as e:
            raise ModelInitializationError("Crash during initialization") from e

        return trainer

    def predict(self, test_samples, model_sess):
        """Make predictions using a pre-loaded trainer

        Keyword arguments:
        :param test_samples: list of samples to make predictions
        :param model_sess: quantized model and its tokenizerOA

        """

        text_samples = [_sample["text"] for _sample in test_samples]

        logger.trace("TEST {}".format(test_samples))

        result_list = []

        for _sample in text_samples:
            logger.trace("{}".format(_sample))

            try:
                encode_dict: BatchEncoding = model_sess["tokenizer"](
                    text=_sample,
                    max_length=self.config["max_seq_length"],
                    truncation=True,
                    return_token_type_ids=self.config["return_token_type_ids"],
                    return_tensors=TensorType.NUMPY,
                )

                logger.trace("encode_dict {}".format(encode_dict))

            except Exception as e:
                raise TokenizerError(
                    "Error tokenizing sample {}".format(_sample)
                ) from e

            try:

                result: np.ndarray = model_sess["model"].run(None, dict(encode_dict))[0]

            except Exception as e:
                raise ModelExecutionError(
                    "Error executing the model for sample {}".format(_sample)
                ) from e

            result_list.append(result[0])

        result_list = np.array(result_list)

        logger.trace("Result_list {}".format(result_list))
        logger.trace("Result NPSHAPE {}".format(np.shape(result_list)))

        def sigmoid_array(x):
            return 1 / (1 + np.exp(-x))

        if self.config["output_mode"] == "multi_label_classification":
            result_list = sigmoid_array(result_list)

            result_class = []

            for _sample in result_list.tolist():

                result_labels = []
                for _idx_label, l in enumerate(_sample):
                    if l > self.config["multi_sigmoid_threshold"]:
                        result_labels.append(self.config["label_list"][_idx_label])

                _result = {"preds": _sample, "labels": result_labels}

                result_class.append(_result)
                confidence = [-1.0 for i in result_class]

        else:
            result_class = result_list.argmax(axis=1)
            result_preds = softmax(result_list, axis=1)

            confidence = np.max(result_preds, axis=1)

            result_class = [
                self.config["label_list"][_class] for _class in result_class.tolist()
            ]

        return result_class, confidence

    def __init__(self, config):
        """Initial stuff"""
        self.config = config
