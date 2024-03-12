import copy
import logging
import re

logger = logging.getLogger("parser.email")


def find_email_text(text):
    regex = r"[\w\.-]+@[\w\.-]+[.]\w{2,5}"
    match = re.findall(regex, text)
    return list(match)


def replace_dat_with_space(text):
    if " @" in text or "@ " in text:
        text = text.replace(" @", "@").replace("@ ", "@")
    return text


def find_emails_with_ocr_errors(
    elements, elements_with_email_list, emails_domains, symbols_replace_at_in_ocr_errors
):
    _elements = copy.deepcopy(elements)
    new_elements_with_email_list = list()

    if elements_with_email_list:
        logger.info(
            "[EMAIL] Emails tagged but not parsed: "
            + str([e.get("text") for e in elements_with_email_list])
        )

    dat_errors = symbols_replace_at_in_ocr_errors

    regex_email_ocr_error = (
        r"("
        + "|".join(dat_errors)
        + r")[a-zA-z\.]+\.(?:"
        + "|".join(emails_domains)
        + r")(?:$|\s)"
    )
    for element in _elements:
        _original = element.get("text")
        if " @" in _original or "@ " in _original:
            corrected_text = replace_dat_with_space(_original)
            element["text"] = corrected_text
            logger.debug("[EMAIL] Corrected {} by {}".format(_original, corrected_text))
            new_elements_with_email_list.append(element)

        match = re.findall(regex_email_ocr_error, element.get("text"))
        match = list(match)
        if match:
            _original = element.get("text")
            corrected_text = _original
            if "@" not in _original:
                for error in dat_errors:
                    corrected_text = corrected_text.replace(error, "@")
                corrected_text = replace_dat_with_space(corrected_text)
                element["text"] = corrected_text
                logger.debug(
                    "[EMAIL] Corrected {} by {}".format(_original, corrected_text)
                )
                new_elements_with_email_list.append(element)

    for element in elements_with_email_list:
        match = re.findall(regex_email_ocr_error, element.get("text"))
        match = list(match)
        if match:
            corrected_text = element.get("text").replace("O", "@").replace("G", "@")
            element["text"] = corrected_text
            new_elements_with_email_list.append(element)

    return new_elements_with_email_list
