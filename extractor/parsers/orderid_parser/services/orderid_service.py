from dateutil import parser
import re


def process_reference_text(orderid_list, remove_words_order_ref):

    black_list_words = ["N.I.F."]

    new_orderid_list = list()
    for order in orderid_list:

        new_txt = order["text"]
        if any([word in new_txt for word in black_list_words]):
            continue
        new_txt = replace_accents(new_txt)
        new_txt = " ".join(new_txt.split())
        for word in remove_words_order_ref:
            pattern = re.compile(re.escape(word.lower()), re.IGNORECASE)
            new_txt = pattern.sub(" ", new_txt)

        new_txt = new_txt.strip()
        new_txt = new_txt.replace("|", "") if new_txt.startswith("|") else new_txt
        new_txt = new_txt.strip()
        order["text"] = new_txt

        new_orderid_list.append(order)

    return new_orderid_list


def replace_accents(txt):
    txt = (
        txt.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )
    txt = (
        txt.replace("ü", "u")
        .replace("à", "a")
        .replace("è", "e")
        .replace("ò", "o")
        .replace("ì", "i")
        .replace("ù", "u")
    )
    return txt





def remove_date_from_order_ref(orderid_list, orderind_list, elements, client):

    dates_in_orderind = ["/Datum"]

    filter_date_of_client = filter_date_for_this_client(client)

    for orderid in orderid_list:
        element_order_id = orderid.get("position_info").get("id_reference_element")
        element_order = get_element_with_id(element_order_id, elements)

        element_ind_id = orderid.get("position_info").get("id_reference_ind")
        element_id = get_element_with_id(element_ind_id, elements)

        if not element_order or not element_id:
            return orderid_list

        elif "DATE" in element_order.get("labels"):
            if filter_date_of_client or any(
                [
                    datestring.lower() in element_id.get("text", "").lower()
                    for datestring in dates_in_orderind
                ]
            ):
                text = " ".join(
                    [
                        w
                        for w in element_order.get("text", "").split()
                        if not is_valid_date(w)
                    ]
                )
                orderid["text"] = text.replace("/", " ").replace("|", " ")

    return orderid_list


def get_element_with_id(id_elem, elements):

    element_with_id_list = [
        elem for elem in elements if elem.get("orig").get("id") == id_elem
    ]
    element = element_with_id_list[0] if element_with_id_list else None
    return element


def is_valid_date(date_str):
    try:
        date = parser.parse(date_str)
        if date.year < 2015 or date.year > 2050:
            return False
        return True
    except:
        return False


def is_orderid_format_element(text, client, group):
    text = text.get("text", "").replace("\n", "").strip()
    if not text:
        return False

    if "," in text:
        return False

    numbers = sum(c.isdigit() for c in text)
    letters = sum(c.isalpha() for c in text)
    spaces = sum(c.isspace() for c in text)
    others = len(text) - numbers - letters - spaces
    text_size = len(text)

    if group == "SOGEDESCA":
        regex_sogedesca_orderid = r"(?i)(?:\s|^)((?:RE|ST)\s*(?:[0-9]|[a-z])\s*(?:[a-z]{1,3}|[0-9]{1,3}}|[0-9,a-z]{1,3})\s*[0-9]{5})"
        pattern = re.compile(regex_sogedesca_orderid)
        if pattern.findall(text):
            return True

    if text_size >= 15:  # too long to be sure
        return False

    if text_size == numbers:
        return True

    if text_size in [others, spaces, letters]:
        return False

    if text_size == numbers + others:
        if text.endswith(".00") or text.endswith(".000") or text.endswith(".0000"):
            return False
        return True

    if numbers >= 0.7 * text_size:
        return True

    # for orderids like cme57622 (companies such as armangue)
    if text.lower().startswith("cme") and numbers >= 0.5 * text_size:
        return True

    if text.lower().startswith("lv") and numbers >= 0.6 * text_size and "/" in text:
        return True

    if numbers >= 0.6 * text_size and ("/" in text or "-" in text):
        return True

    return False


def clean_orderinds(orderind_elems, blacklist_words):

    blacklist_words = [replace_accents(w.lower()) for w in blacklist_words]
    new_orderind_list = list()
    for orderind in orderind_elems:
        text = replace_accents(orderind.get("text").lower())
        if any([w.lower() in text for w in blacklist_words]):
            continue

        new_orderind_list.append(orderind)

    return new_orderind_list


def filter_date_for_this_client(client):
    clients_filter_Date = ["FERROINSA FORTES, S.L."]
    if client and client in clients_filter_Date:
        return True
    return False


def get_orderid_of_body_tag(element, data):
    text = element.get("text")
    id_elem = element.get("orig").get("id")
    replacers = ["#", "reference", "ref", "\n", ":"]
    text_clean_ind = text
    for replacer in replacers:
        text_clean_ind = re.sub(replacer, "", text_clean_ind, flags=re.IGNORECASE)
    text_clean_ind = text_clean_ind.strip()

    if any(c.isalpha() or c.isdigit() for c in text_clean_ind):
        return [text_clean_ind.strip()], [id_elem]
    else:
        next_elem = _get_element_with_a_given_id(data, id_elem + 1)
        text_next = next_elem.get("text")
        id_next = next_elem.get("orig").get("id")
        if not any(c.isalpha() for c in text_next):
            next_elem = _get_element_with_a_given_id(data, id_elem + 2)
            text_next = next_elem.get("text")
            id_next = next_elem.get("orig").get("id")
        company = text_next.strip()
        element_id_list = [id_elem, id_next]
    return [company], element_id_list


def _get_element_with_a_given_id(data, id) -> list[int]:
    for page in data:
        elements = page.get("elements")
        for element in elements:
            if element.get("orig").get("id") == id:
                return element
    return None
