import logging
import dateparser
import spacy

logger = logging.getLogger("parser.person")

nlp = spacy.load("xx_ent_wiki_sm")  # Load multilingual model


def extract_person_name_from_string(dat: str) -> list:
    """Extract names of persons from one element

    Args:
      dat: string to search for a name

    Returns:
      Array with names founded in a string

    """
    person_list = []
    string_preprocessed = preprocess_string_chain(dat)
    ner_ent = nlp(string_preprocessed)

    if ner_ent.ents:
        for ent in ner_ent.ents:
            if ent.label_ == "PER":
                person_list.append(ent.text)

    if not person_list and len(dat.split()) < 5:
        person_list.append(dat)

    return person_list


def preprocess_string_chain(dat: str) -> str:
    string_lower = dat.lower()
    string_cap = string_lower.title()

    return string_cap
