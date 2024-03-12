import re
import logging
import stdnum.gb.vat as gbvat
from extractor.pyvat import pyvat

logger = logging.getLogger("parser.cif")


def clean_element(text):

    cif_remove_words = [
        "VAT Reg. No.",
        "V.A.T. No.:",
        "cif",
        "c1f",
        "c.i.f.",
        "c.1.f.",
        "vat",
        "V.A.T.",
        "NIPC",
        "NIF",
        "N.I.F.",
        "tva",
        "N° Intracom.",
        "btw-nr",
        "btw",
    ]

    punct_remove = [":", "."]
    for word in cif_remove_words + punct_remove:
        compiled = re.compile(re.escape(word), re.IGNORECASE)
        text = compiled.sub(" ", text)

    text = re.sub(" +", " ", text)
    text = text.strip()
    return text


def extract_cif_from_element(text):

    text = text.strip()

    # solve potential OCR errors
    text = text.replace("O", "0")

    if text.startswith(":"):
        text = text.replace(":", "")
    text = text.replace("-", "").replace(".", "")

    if gbvat.is_valid(text):
        cif_text = gbvat.validate(text)
        return cif_text, None

    cif = pyvat.check_vat_number(text, country_code=None)
    if cif.is_valid:
        return text, cif.business_name

    text_repl = re.sub(r"^([a-zA-Z]+-?)(?:[0-9]+)", "", text)
    if text == text_repl:
        return None, None
    cif = pyvat.check_vat_number(text, country_code=None)
    if cif.is_valid:
        return text, cif.business_name

    return None, None


def has_cif_word(text, cif_indicators):
    text = text.replace(".", "")
    text = text.replace(":", "")
    for ind in cif_indicators:
        text = text.replace(ind, ind + " ")
    text = re.sub(" +", " ", text)

    for indicator in cif_indicators:
        indicator = indicator.lower()
        if " " + indicator + " " in " " + text + " ":
            return True
        if " " + indicator + ":" in " " + text + " ":
            return True
        if " " + indicator + "." in " " + text + " ":
            return True

    return False


def cif_text_not_empty(text):
    if text and text not in ["", " ", "  "]:
        return True

    return False


def get_cif_from_line(text, indicators):
    text = text.replace(".", " ").replace(":", " ")
    text = " ".join(text.split())  # remove double spaces

    indicators = [ind.replace("(", "\(").replace(")", "\)") for ind in indicators]
    regex = r"(?i)(?:" + "|".join(indicators) + r")(?:\s*)([0-9,\s{0,1}]+)"
    found = re.search(regex, text)
    if found:
        cif_text = found.group(1)
        logger.info("complete text: " + str(text))
        logger.info("found cif text regex 1: " + str(cif_text))
        if cif_text_not_empty(cif_text):
            return cif_text

    regex = (
        r"(?i)(?:"
        + "|".join(indicators)
        + r")(?:\s*)((?:[a-zA-Z]{2,3}|B|A)\s?(?:[0-9]+[a-zA-Z]?)+)"
    )
    text_intermediate_processed = re.sub(r"(\d)\s+(B0)", r"\1\2", text)
    text_without_spaces_between_digits = re.sub(
        r"(\d)\s+(\d)", r"\1\2", text_intermediate_processed
    )
    found = re.search(regex, text_without_spaces_between_digits)
    if found:
        logger.info("complete text: " + str(text))
        cif_text = found.group(1)
        logger.info("found cif text regex 2: " + str(cif_text))
        if cif_text_not_empty(cif_text):
            return cif_text

    return None
