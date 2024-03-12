from extractor.common.infraestructure.ElasticClient import ElasticConnection
import logging

logger = logging.getLogger("controller.elastic")

elastic_indices = {
    "INDEX_CLIENTS": None,
    "INDEX_PRODUCTS": None,
    "INDEX_ADDRESSES": None,
    "INDEX_TRUCKS": None,
    "INDEX_BILLING_COMPANY": None,
    "INDEX_QUALITY": None,
    "INDEX_CONVERSIONS": None,
}


def get_elastic_client(config):

    global elastic_indices
    elastic_client = ElasticConnection(
        config["ip"], config["port"], config["user_elastic"], config["password_elastic"]
    )
    set_elastic_indices_name(config["indices"])

    return elastic_client


def set_elastic_indices_name(indices):
    global elastic_indices
    elastic_indices["INDEX_CLIENTS"] = indices["clients"]
    elastic_indices["INDEX_PRODUCTS"] = indices["products"]
    elastic_indices["INDEX_ADDRESSES"] = indices["addresses"]
    elastic_indices["INDEX_TRUCKS"] = indices["trucks"]
    elastic_indices["INDEX_BILLING_COMPANY"] = indices["billing_company"]
    elastic_indices["INDEX_QUALITY"] = indices["qualities"]
    elastic_indices["INDEX_CONVERSIONS"] = indices["conversions"]
