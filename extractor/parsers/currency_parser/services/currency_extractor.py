import logging
import re

logger = logging.getLogger("parser.currency")


def find_currency(text, currency_alias):

    text = text.lower()
    results = list()
    for currency in currency_alias:
        already_match = False
        for term in currency_alias[currency]:
            if term in text and not already_match:
                already_match = True
                score = "NORMAL"
                regex_isolated_symbol = (
                    r"(?i)(?:^|\s|\(|[0-9])" + re.escape(term) + r"(?:$|\/|\s|\)|[0-9])"
                )
                match = list(
                    re.findall(
                        regex_isolated_symbol, text.replace("\n", "").replace("\t", "")
                    )
                )
                if match:
                    score = "NORMAL"
                    # logger.info("currency score: NORMAL - " + str(text))
                else:
                    score = "LOW"
                    # logger.info("currency score: LOW - " + str(text))
                results.append((currency, score))
    return list(set(results))
