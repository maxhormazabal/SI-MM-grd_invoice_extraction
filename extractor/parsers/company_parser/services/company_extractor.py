import re
import logging
import spacy

logger = logging.getLogger("parser.company")

nlp = spacy.load("xx_ent_wiki_sm")  # Load multilingual model


def extract_companies_from_element(element: str, use_orig=True) -> list:
    """Extract companies from an element

    Args:
      element: string to search for a company name

    Returns:
      Array with companies founded in a string

    """
    text = (
        element.get("orig").get("text").rstrip("\n")
        if use_orig
        else element.get("text")
    )
    labels = element["labels"]

    companies_list = []
    if "NOTE" in labels or len(text) > 100:
        companies_list = extract_company_entity(text)

    if (
        any(
            lab in labels
            for lab in ["ADDRESS1", "ADDRESSX", "EMAIL", "PERSON", "CURRENCY"]
        )
        and len(text) > 55
    ):
        companies_list = extract_company_entity(text)

    if not companies_list:
        companies_list = [text.rstrip("\n")]

    return companies_list


def extract_company_entity(text):

    company_list = []
    string_preprocessed = preprocess_string_chain(text)

    company_text, found = direct_match_company_name(string_preprocessed)
    if found:
        company_list.append(company_text)
    if company_list:
        return company_list

    ner_ent = nlp(string_preprocessed)
    if ner_ent.ents:
        for ent in ner_ent.ents:
            if ent.label_ == "ORG":
                company_list.append(ent.text)

    if not company_list:
        splitted_text = text.lower().split()
        matches = [
            x
            for x in [
                "s.a.",
                "s.l.",
                "sa",
                "sa,",
                "sl",
                "sl,",
                "ltd",
                "ltd,",
                "limited",
                "limited,",
                "bv",
                "oy",
                "gmbh",
                "logistics",
            ]
            if x in splitted_text
        ]
        if matches:
            match = matches[0]
            index_match = splitted_text.index(match)
            if index_match > 4:
                result = (
                    " ".join(splitted_text[index_match - 3 : index_match]) + " " + match
                )
            else:
                result = " ".join(splitted_text[:index_match]) + " " + match
            company_list.append(result)

    if not company_list and len(text.split()) < 5:
        company_list.append(text)

    return company_list


def preprocess_string_chain(text: str) -> str:
    string_lower = text.lower()
    string_cap = string_lower.title()

    return string_cap


def direct_match_company_name(text):
    company_names = ["juamba materiales de construccion y ferrallas sl"]

    for company_name in company_names:
        if text.lower() in company_name:
            return company_name, True

    return None, False


def get_company_of_body_tag(element, elements_list):
    text = element.get("text")
    id_elem = element.get("orig").get("id")
    replacers = ["#", "cliente", "client", "cli", "\n", ":"]
    text_clean_ind = text
    for replacer in replacers:
        text_clean_ind = re.sub(replacer, "", text_clean_ind, flags=re.IGNORECASE)
    text_clean_ind = text_clean_ind.strip()

    if any(c.isalpha() for c in text_clean_ind):
        return [text_clean_ind.strip()], [id_elem]
    else:
        next_elem = _get_element_with_a_given_id(elements_list, id_elem + 1)
        text_next = next_elem.get("text")
        id_next = next_elem.get("orig").get("id")
        if not any(c.isalpha() for c in text_next):
            next_elem = _get_element_with_a_given_id(elements_list, id_elem + 2)
            text_next = next_elem.get("text")
            id_next = next_elem.get("orig").get("id")
        company = text_next.strip()
        element_id_list = [id_elem, id_next]
    return [company], element_id_list


def _get_element_with_a_given_id(elements, id) -> list[int]:
    for element in elements:
        if element.get("orig").get("id") == id:
            return element
    return None


def clean_company_name_in_subject_of_email(element):
    remove_terms = [
        "asunto",
        "///",
        "//",
        "pedido nuevo a introducir",
        "NUEVO PEDIDO A INTRODUCIR",
        "pedido",
        "muchas gracias",
    ]
    element["text"] = replace_substring(element.get("text"), "", remove_terms)
    return element


def replace_substring(text, repl, remove_terms):
    regex = re.compile("|".join(remove_terms), flags=re.IGNORECASE)
    txt = regex.sub(repl, text)
    return txt
