import os


def process_env_variables_gen(config_gen):

    return config_gen


def process_env_variables_ocr(config_ocr):
    if os.getenv("OCR_HOST"):
        config_ocr["ocr"]["HOSTNAME"] = os.getenv("OCR_HOST")
    if os.getenv("OCR_PORT"):
        config_ocr["ocr"]["PORT"] = os.getenv("OCR_PORT")

    return config_ocr


def process_variables_ext(config_extractor, path):
    config_extractor["onnx"]["multi"]["model_name_or_path"] = os.path.join(
        path, config_extractor["onnx"]["multi"]["model_name_or_path"]
    )
    config_extractor["onnx"]["multi"]["tokenizer_name"] = os.path.join(
        path, config_extractor["onnx"]["multi"]["tokenizer_name"]
    )
    config_extractor["onnx"]["single"]["model_name_or_path"] = os.path.join(
        path, config_extractor["onnx"]["single"]["model_name_or_path"]
    )
    config_extractor["onnx"]["single"]["tokenizer_name"] = os.path.join(
        path, config_extractor["onnx"]["single"]["tokenizer_name"]
    )
    config_extractor["parsers"]["currency_parser"][
        "currency_config_file"
    ] = os.path.join(
        path, config_extractor["parsers"]["currency_parser"]["currency_config_file"]
    )

    config_extractor["parsers"]["product_parser"]["product_description_parser"][
        "qualities_files"
    ]["internal_quality"] = os.path.join(
        path,
        config_extractor["parsers"]["product_parser"]["product_description_parser"][
            "qualities_files"
        ]["internal_quality"],
    )
    config_extractor["parsers"]["product_parser"]["product_description_parser"][
        "qualities_files"
    ]["external_quality"] = os.path.join(
        path,
        config_extractor["parsers"]["product_parser"]["product_description_parser"][
            "qualities_files"
        ]["external_quality"],
    )
    config_extractor["parsers"]["product_parser"]["product_description_parser"][
        "qualities_files"
    ]["external_norm"] = os.path.join(
        path,
        config_extractor["parsers"]["product_parser"]["product_description_parser"][
            "qualities_files"
        ]["external_norm"],
    )
    config_extractor["parsers"]["product_parser"]["product_description_parser"][
        "product_alias"
    ] = os.path.join(
        path,
        config_extractor["parsers"]["product_parser"]["product_description_parser"][
            "product_alias"
        ],
    )
    config_extractor["parsers"]["currency_parser"][
        "currency_config_file"
    ] = os.path.join(
        path, config_extractor["parsers"]["currency_parser"]["currency_config_file"]
    )

    return config_extractor


def process_env_variables_desambiguator(config_des, path):

    return config_des


def process_env_variables_directories(config_directories, path):
    config_directories["general_directories"]["product_desambiguator"][
        "exceptions"
    ] = os.path.join(
        path,
        config_directories["general_directories"]["product_desambiguator"][
            "exceptions"
        ],
    )

    config_directories["general_directories"]["product_desambiguator"][
        "names_to_category_file"
    ] = os.path.join(
        path,
        config_directories["general_directories"]["product_desambiguator"][
            "names_to_category_file"
        ],
    )
    config_directories["general_directories"]["product_desambiguator"][
        "prices_by_company_file"
    ] = os.path.join(
        path,
        config_directories["general_directories"]["product_desambiguator"][
            "prices_by_company_file"
        ],
    )


    return config_directories
