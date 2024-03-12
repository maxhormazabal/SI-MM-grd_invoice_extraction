import logging

# sys.path.append(os.path.abspath(".."))
import elasticsearch
from elasticsearch import Elasticsearch

from extractor.common.controllers.custom_exceptions import ElasticDesambiguationError

logger = logging.getLogger("infra.elastic")


class ElasticConnection:
    def __init__(self, ip, port, user, password):
        logger.debug("Creating ElasticSearch connection")
        self.es_client = Elasticsearch(
            hosts=["https://" + ip + ":" + str(port)],
            verify_certs=False,
            http_auth=(user, password),
        )
        self.elastic_special_chars = [
            "+",
            "-",
            "=",
            "&&",
            "||",
            ">",
            "<",
            "!",
            "(",
            ")",
            "{",
            "}",
            "[",
            "]",
            "^",
            '"',
            "~",
            "*",
            "?",
            ":",
            "\\",
            "/",
        ]

    def make_elastic_request(self, index, body, size=None):
        """

        Parameters
        ----------
        index - Name of an index
        body - Body of the query to be executed
        size - size of results that Elastic will return. If size is None or False, the default size is 10.

        Returns - Result obtained from ElasticSearch
        -------

        """
        try:
            if size:
                result = self.es_client.search(index=index, body=body, size=size)
            else:
                result = self.es_client.search(index=index, body=body)
        except elasticsearch.exceptions.NotFoundError as exc:
            logger.error(
                "Error finding data in Elastic server - {}".format(exc.message)
            )
            raise ElasticDesambiguationError(exc)
        except ConnectionError as exc:
            logger.error(
                "{} - Connection error with Elastic server: {}".format(
                    exc.__class__.__name__, exc
                )
            )
            raise ElasticDesambiguationError(exc)
        except Exception as exc:
            logger.error(
                "{} - Some error ocurred with ElasticSearch searching: {}".format(
                    exc.__class__.__name__, exc
                )
            )
            raise ElasticDesambiguationError(exc)

        return result

    def scape_chars_elastic(self, text):
        """
        Scapes the text in order that it does not lead to an Exception when used in a query to elastic search
        Parameters
        ----------
        text - text

        Returns text scaped
        -------

        """
        text = "".join(
            [
                "\\" + char if char in self.elastic_special_chars else char
                for char in text
            ]
        )
        return text
