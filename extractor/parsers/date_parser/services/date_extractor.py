import logging
import re

import dateparser
import datetime
from calendar import month_name

logger = logging.getLogger("parser.date")
months = {m.lower() for m in month_name[1:]}


def extract_dates_from_string(dat: str) -> list:
    """Extract dates from one element

    Args:
      dat: string to search for a date

    Returns:
      Array with dates founded in a string

    """

    dat, format_detected = transform_strange_formats(dat)
    actual_year = datetime.datetime.now().year
    result = dateparser.parse(dat, settings={"DATE_ORDER": format_detected})
    result_formatter = dat
    success = False
    if result and valid_date(dat):
        if not any(chr.isdigit() for chr in dat):
            result = result.replace(day=1)
        result_formatter = result.strftime("%d-%m-%Y")
        success = True

    elif "sem." in dat.lower():
        date = dat.split(" ")
        if len(date) > 0 and re.match(r"^([0-9][0-9]\.20[1-4][0-9])", date[1]):
            result = datetime.datetime.strptime(date[1] + ".1", "%W.%Y.%w")
        elif re.match(r"^([0-9][0-9])", date[1]):
            result = datetime.datetime.strptime(
                date[1] + "." + str(actual_year) + ".1", "%W.%Y.%w"
            )
        if result:
            result_formatter = result.strftime("%d-%m-%Y")
            success = True

    elif valid_date(dat):
        date_string_split = dat.split(" ")
        for date in date_string_split:
            if any(chr.isdigit() for chr in date):
                date, format_detected = transform_strange_formats(date)
                result = dateparser.parse(
                    date, settings={"DATE_ORDER": format_detected}
                )
                if result and valid_date(date):
                    if (result.year <= actual_year + 2) and (result.year > 2010):
                        result_formatter = result.strftime("%d-%m-%Y")
                        success = True
                        return result_formatter, success
                else:
                    result = dateparser.parse(date, settings={"DATE_ORDER": "YMD"})
                    if result and valid_date(date):
                        result_formatter = result.strftime("%d-%m-%Y")
                        success = True
                        return result_formatter, success
    else:
        result_formatter = ""
        success = False

    return result_formatter, success


def transform_strange_formats(string):
    result = string
    format_result = "DMY"
    if re.match(r"^([0-1]?[0-9]\-20[1-4][0-9])", string):
        result = "1-" + string

    elif re.match(r"^(20[1-4][0-9]\.[0-1]?[0-9]\.[0-3][0-9])", string):
        format_result = "YMD"

    elif re.match(r"^([0-3][0-9][0-1]?[0-9][1-4][0-9])$", string):
        result = string[0:2] + "/" + string[2:4] + "/" + string[4:6]
        format_result = "DMY"

    elif string.startswith("MÀXIMO"):
        result = string.replace("MÀXIMO", "").replace("EN DESTINO", "")

    elif string.lower().endswith("shipment"):
        result = string.lower().replace("shipment", "")

    elif "week" in string.lower():
        dates_candidates = [s for s in re.findall(r"-?\d+\.?\d*", string.lower())]
        if len(dates_candidates) >= 1:
            result = "sem. " + dates_candidates.__getitem__(0)
    elif re.match(r"^([0-1]?[0-9]/[1-4][0-9]$)", string):
        result = "1/" + string  # firstday
    elif re.match(r"^([0-1][0-9]\.20[1-4][0-9])", string):
        result = "01/" + string[0:2] + "/" + string[3:]
    elif re.search(r"\s*(\d{2}-\d{2}-\d{4})\s*", string):
        result = re.search(r"\s*(\d{2}-\d{2}-\d{4})\s*", string).group(1)
    elif re.search(r"(?i)([0-3][0-9]\sde\s[a-z])", string):
        day = re.search(r"(?i)[0-3][0-9]\sde", string).group(0)
        month = string.split()[string.lower().split().index("de") + 1]
        result = day + " " + month
    elif re.search(r"(20[1-4][0-9]\s)", string) and re.search(
        r"\b({})\b".format("|".join(months)), string, re.IGNORECASE
    ):
        month = re.search(
            r"\b({})\b".format("|".join(months)), string, re.IGNORECASE
        ).group(1)
        year = re.search(r"(20[1-4][0-9]\s)", string).group(1)
        result = "01-" + month + "-" + year
    elif re.search(r"\b\d{2}/\d{2}/\d{4}\b", string):
        result = re.search(r"\d{2}/\d{2}/\d{4}\b", string).group()

    return result, format_result


def valid_date(string):
    if re.match(r"(^20[1-4][0-9]$)", string):  # year without month
        return False
    if re.search(r"(\d\d\.\d\d\.\d\d\.\d\d)", string):  # false date
        return False
    elif len(string.split()) > 8:  # annotation
        return False
    elif "referencia" in string.lower():
        return False
    else:
        return True
