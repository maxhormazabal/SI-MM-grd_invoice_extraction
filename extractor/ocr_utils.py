import re
import logging
import time
import requests
import os
import json
import traceback
from statistics import mean, median, mode
from extractor.common.cli.logging import get_elapsed_time_message, configure_logger
from extractor.pdfreader.camelotreader.usecases.pdf_to_extractor_usecase import (
    PDFExtractorUseCase,
)
from extractor.formatters.ocr_conversor.usecases.ocr_conversor_usecase import (
    OCRConversorUseCase,
)
from extractor.labellers.onnx_class.usecases.tag_documents_usecase import (
    TagDocumentsUseCase,
)


DEFAULT_PAGE_WIDTH = 842
DEFAULT_PAGE_HEIGHT = 595

logger = logging.getLogger("extractor")


def run_camelot_or_ocr_and_tagging(
    use_camelot, path, index, doc, ocr_config, extractor_config
):
    logger.info("Processing document (" + str(index) + "): " + doc)
    general_start_time = time.time()
    start_time = general_start_time
    processing_output_ocr, processed_with_ocr = process_file_for_parse(
        path, ocr_config, extractor_config, use_camelot
    )
    # 4- Etiquetador de regiones #########################
    start_time = time.time()
    lines_and_elements_tagged = TagDocumentsUseCase(
        extractor_config["onnx"], processing_output_ocr
    ).execute()
    logger.info(get_elapsed_time_message("phase 2: region tagging", start_time))
    return lines_and_elements_tagged, processed_with_ocr


def process_file_for_parse(
    doc_path, config_ocr, config_extractor, default_camelot=True,
):
    output = None
    output_camelot = {}
    process_with_ocr = False
    # 1- CAMELOT
    if default_camelot:
        logger.info("Processing document with Camelot")
        try:
            output = PDFExtractorUseCase(
                config_ocr["pdf_conversor"], doc_path
            ).execute()
            output_camelot = output
            if not is_camelot_output_valid(
                output,
                config_ocr["camelot"]["minimum_median_length_elements_to_be_valid"],
            ):
                process_with_ocr = True
                logger.info("Camelot output is not valid")

        except Exception:
            logger.debug(traceback.format_exc())
            logging.getLogger("pdfreader.camelot").warning(
                "Could not process the file with camelot"
            )
            process_with_ocr = True
    else:
        process_with_ocr = True

    page_widhts, page_heights = get_page_dimensions(output)

    if process_with_ocr:
        logger.info("Processing document with OCR")
        # 2 - OCR
        # 2.1- detectamos el idioma del pdf
        try:
            language = get_language_from_document(doc_path, config_ocr["ocr"])
            logger.info("Language detected by OCR: " + str(language))
            # 2.2- llamamos al ocr
            output = process_document_with_ocr(doc_path, config_ocr["ocr"], language)
            output = OCRConversorUseCase(
                config_extractor["ocr_conversor"], output
            ).execute(page_widhts, page_heights)


        except Exception:
            logger.debug(traceback.format_exc())
            logging.getLogger("infra.ocr").warning(
                "Could not process the file with ocr"
            )
    return output, process_with_ocr


def get_language_from_document(file_path, config):
    logging.getLogger("infra.ocr").debug("Getting language with OCR module")
    start_time = time.time()

    url = "http://" + config["HOSTNAME"] + ":" + str(config["PORT"]) + "/"
    files = {
        "document": (
            os.path.basename(file_path),
            open(file_path, "rb"),
            "application/pdf",
        )
    }
    payload = {"rasterize": True}
    result = requests.post(
        url=url + config["URL_language"], files=files, data=payload
    ).content.decode()

    result = json.loads(result)[0]
    language = max(result.items(), key=lambda x: x[1])[0]

    logging.getLogger("infra.ocr").trace("Language found: " + language + ")")
    logging.getLogger("infra.ocr").debug(
        get_elapsed_time_message("getting language", start_time)
    )

    supported_langs = [
        "bel",
        "cat",
        "deu",
        "eng",
        "fra",
        "glg",
        "ita",
        "osd",
        "por",
        "spa",
    ]

    if language not in supported_langs:
        logger.info(
            "Language "
            + str(language)
            + " not supported by the OCR. English selected as default."
        )
        language = "eng"

    return language


def process_document_with_ocr(file_path, config, language):
    logging.getLogger("infra.ocr").debug("Processing document with OCR")
    start_time = time.time()

    url = "http://" + config["HOSTNAME"] + ":" + str(config["PORT"]) + "/"
    files = {
        "document": (
            os.path.basename(file_path),
            open(file_path, "rb"),
            "application/pdf",
        )
    }
    payload = {"language": language, "rasterize": True}
    result = requests.post(
        url=url + config["URL_analize"], files=files, data=payload
    ).content.decode()

    logging.getLogger("infra.ocr").debug(
        get_elapsed_time_message("process with OCR", start_time)
    )

    return json.loads(result)


def is_camelot_output_valid(output, minimum_median_length_elements_to_be_valid):
    if len(output["data"][0]["elements"]) == 0:
        return False

    page1 = output["data"][0]["elements"]
    if output.get("is_email_file"):
        lens_chars = [
            len(x["text"])
            for x in page1
            if x.get("text") not in [r"\n", "\n", "\xa0\n"]
        ]
    else:
        lens_chars = [len(x["text"]) for x in page1]
    median_value = median(lens_chars)
    if median_value < minimum_median_length_elements_to_be_valid:
        return False

    # Solve problem with CIDs
    txt = " ".join([x["text"] for x in page1])
    cids_charcters = re.findall(r"\(cid\:(\d+)\)", txt)
    if cids_charcters and len(cids_charcters) >= len(page1):
        return False

    return True

def get_page_dimensions(output):

    if not output:
        return [DEFAULT_PAGE_WIDTH], [DEFAULT_PAGE_HEIGHT]

    page_widths, page_heights = [], []
    for page in output.get("data"):
        page_widths.append(page.get("width", DEFAULT_PAGE_WIDTH))
        page_heights.append(page.get("height", DEFAULT_PAGE_HEIGHT))
    return page_widths, page_heights


def fix_hashtags_last_page(data):
    try:
        if is_hybrid_order(data):
            num_pages = len(data.get("data"))
            last_page = data.get("data")[num_pages - 1]
            num_lines_last_page = len(last_page.get("lines"))
            if num_lines_last_page < 15:
                REGEX_SUBS_WRONG_CLI = [r"(?i)^(?:.{1,4})(", r")(?:$|\s|:)", r"#CLI "]
                replace_inds = [r"c\i", r"cii", r"cll", r"CIli"]
                last_page = replace_tags(last_page, REGEX_SUBS_WRONG_CLI, replace_inds)

                REGEX_SUBS_WRONG_HASHTAG = [r"(?i)^(?:.{1,4})(", r")", r"#\1"]
                replace_inds = [
                    "cli",
                    "pb",
                    "base",
                    "pf",
                    "fin",
                    "pro",
                    "fec",
                    "inc",
                    "dir",
                    "ref",
                ]
                last_page = replace_tags(
                    last_page, REGEX_SUBS_WRONG_HASHTAG, replace_inds
                )
        if data.get("is_email_file"):
            for page in data.get("data"):
                REGEX_SUBS_WRONG_CLI = [r"(?i)^(?:.{1,4})(", r")(?:$|\s|:)", r"#CLI "]
                replace_inds = [r"c\i", r"cii", r"cll", "CIli"]
                page = replace_tags(page, REGEX_SUBS_WRONG_CLI, replace_inds)

                REGEX_SUBS_WRONG_HASHTAG = [r"(?i)^(?:.{1,4})(", r")", r"#\1"]
                replace_inds = [
                    "cli",
                    "pb",
                    "base",
                    "pf",
                    "fin",
                    "pro",
                    "fec",
                    "inc",
                    "dir",
                    "ref",
                ]
                page = replace_tags(page, REGEX_SUBS_WRONG_HASHTAG, replace_inds)
    except Exception:
        logger.error(traceback.format_exc())
        logger.error("Error in fix_hashtags_last_page")
    return data


def replace_tags(page, REGEX_SUBS_WRONG_HASHTAG, replace_inds):
    for elem in page.get("elements"):
        elem = replace_tags_elem(elem, replace_inds, REGEX_SUBS_WRONG_HASHTAG)
    for line in page.get("lines"):
        line = replace_tags_lines(line, replace_inds, REGEX_SUBS_WRONG_HASHTAG)
    return page


def replace_tags_elem(elem, replace_inds, REGEX_SUBS_WRONG_HASHTAG):
    for ind in replace_inds:
        elem["text"] = re.sub(
            REGEX_SUBS_WRONG_HASHTAG[0] + re.escape(ind) + REGEX_SUBS_WRONG_HASHTAG[1],
            REGEX_SUBS_WRONG_HASHTAG[2],
            elem.get("text"),
        )
        elem["orig"]["text"] = re.sub(
            REGEX_SUBS_WRONG_HASHTAG[0] + re.escape(ind) + REGEX_SUBS_WRONG_HASHTAG[1],
            REGEX_SUBS_WRONG_HASHTAG[2],
            elem.get("orig").get("text"),
        )
    return elem


def replace_tags_lines(line, replace_inds, REGEX_SUBS_WRONG_HASHTAG):
    for ind in replace_inds:
        line["text"] = re.sub(
            REGEX_SUBS_WRONG_HASHTAG[0] + re.escape(ind) + REGEX_SUBS_WRONG_HASHTAG[1],
            REGEX_SUBS_WRONG_HASHTAG[2],
            line.get("text"),
        )
        line["orig"][0]["text"] = re.sub(
            REGEX_SUBS_WRONG_HASHTAG[0] + re.escape(ind) + REGEX_SUBS_WRONG_HASHTAG[1],
            REGEX_SUBS_WRONG_HASHTAG[2],
            line.get("orig")[0].get("text"),
        )
    return line


def is_hybrid_order(lines_and_elements_tagged):
    if not lines_and_elements_tagged:
        return False

    if "data" in lines_and_elements_tagged:
        if (
            lines_and_elements_tagged.get("data", [{}])[0]
            .get("source", "")
            .startswith("ind_")
        ):
            return True
    elif "source" in lines_and_elements_tagged:
        if lines_and_elements_tagged.get("source", "").startswith("ind_"):
            return True
    return False


def set_last_page_camelot_when_inds(
    lines_and_elements_tagged, lines_and_elements_tagged_ocr, last_page
):
    if is_hybrid_order(lines_and_elements_tagged):
        logger.info("Substituting last page of OCR by last page of camelot")
        lines_and_elements_tagged_ocr["data"][-1] = last_page
    return lines_and_elements_tagged_ocr
