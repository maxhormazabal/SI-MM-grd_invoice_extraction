import argparse
import re
import copy
import logging
import os.path
import traceback
import time
import threading

import requests
from kafka import KafkaConsumer
from extractor.ocr_utils import (
    process_file_for_parse,
    run_camelot_or_ocr_and_tagging,
    is_hybrid_order,
    set_last_page_camelot_when_inds,
)
from extractor.common.cli.logging import get_elapsed_time_message, configure_logger
from extractor.common.cli.utils import read_yaml, write_json, remove_locally_file
from extractor.common.configuration.config import (
    process_env_variables_gen,
    process_env_variables_ocr,
    process_env_variables_desambiguator,
    process_variables_ext,
    process_env_variables_directories,
)


from extractor.labellers.onnx_class.usecases.tag_documents_usecase import (
    TagDocumentsUseCase,
)

from extractor.parsers.address_parser.usecases.address_parser import (
    AddressParserUseCase,
)
from extractor.parsers.CIF_parser.usecases.CIF_parser import CIFParserUseCase
from extractor.parsers.company_parser.usecases.company_parser import (
    CompanyParserUseCase,
)
from extractor.parsers.currency_parser.usecases.currency_parser import (
    CurrencyParserUseCase,
)
from extractor.parsers.date_parser.usecases.date_parser import DateParserUseCase
from extractor.parsers.deliveryaddress_parser.usecases.deliveryaddress_parser import (
    DeliveryAddressParserUseCase,
)
from extractor.parsers.email_parser.usecases.email_parser import EmailParserUseCase

from extractor.parsers.note_parser.usecases.note_parser import NoteParserUseCase
from extractor.parsers.orderid_parser.usecases.orderid_parser import (
    OrderIDParserUseCase,
)
from extractor.parsers.payment_parser.usecases.payment_parser import (
    PaymentParserUseCase,
)
from extractor.parsers.person_parser.usecases.person_parser import PersonParserUseCase

from extractor.parsers.truck_note_parser.usecases.truck_note_parser import (
    TruckNoteParserUseCase,
)


# Disable warning with urllib3 into requests package
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

logger = logging.getLogger("extractor")


def get_config(base_path):
    return (
        read_yaml(os.path.join(base_path, "common/configuration/connection_conf.yml")),
        read_yaml(
            os.path.join(base_path, "common/configuration/fileprocessor_conf.yml")
        ),
        read_yaml(os.path.join(base_path, "common/configuration/parser_conf.yml")),
        read_yaml(os.path.join(base_path, "common/configuration/elastic_config.yml")),
        read_yaml(os.path.join(base_path, "common/configuration/general_conf.yml")),
        read_yaml(os.path.join(base_path, "common/configuration/log_config.yml")),
    )


def get_env_variables(
    system_config,
    ocr_config,
    extractor_config,
    desambiguator_config,
    general_conf,
    log_config,
):
    return (
        process_env_variables_gen(system_config),
        process_env_variables_ocr(ocr_config),
        process_variables_ext(
            extractor_config, os.path.dirname(os.path.abspath(__file__))
        ),
        process_env_variables_desambiguator(
            desambiguator_config, os.path.dirname(os.path.abspath(__file__))
        ),
        process_env_variables_directories(
            general_conf, os.path.dirname(os.path.abspath(__file__))
        ),
        log_config,
    )


(
    system_config,
    ocr_config,
    extractor_config,
    desambiguator_config,
    general_config,
    log_config,
) = get_config(os.path.dirname(os.path.abspath(__file__)))
(
    system_config,
    ocr_config,
    extractor_config,
    desambiguator_config,
    general_config,
    log_config,
) = get_env_variables(
    system_config,
    ocr_config,
    extractor_config,
    desambiguator_config,
    general_config,
    log_config,
)


def tag_with_parsers(tagged_lines, config):
    # company, cif, email address  and deliveryaddress already executed

    result = CIFParserUseCase(
        config.get("cif_parser"), tagged_lines
    ).execute()

    result = EmailParserUseCase(
        result, config.get("email_parser")
    ).execute()

    result = CompanyParserUseCase(result).execute()

    result = AddressParserUseCase(
        config.get("address_parser"), result
    ).execute()

    result = DeliveryAddressParserUseCase(
        config.get("deliveryaddress"), result
    ).execute()

    result = copy.deepcopy(result)

    # 1- Note parser
    result = NoteParserUseCase(config["note_parser"], result).execute()

    # 1.1- Truck note parser
    result = TruckNoteParserUseCase(result).execute()

    # 5- Date parser
    result = DateParserUseCase(result, config["deliverydate"]).execute()

    # 7- Person parser
    result = PersonParserUseCase(result).execute()

    # 8- Product parser
    #result = ProductParserUseCase(config["product_parser"], result).execute()

    # 9- Order id parser
    result = OrderIDParserUseCase(config["orderid"], result).execute()

    # 12- payment parser
    result = PaymentParserUseCase(config["payment_note"], result).execute()

    # 13 - Currency parser
    result = CurrencyParserUseCase(result, config["currency_parser"]).execute()

    return result


def process_order(
    doc, path, index, use_camelot=True
):
    if use_camelot:
        lines_and_elements_tagged, processed_with_ocr = run_camelot_or_ocr_and_tagging(
            use_camelot, path, index, doc, ocr_config, extractor_config
        )
        final_result, processed_with_ocr, class_output = process_order_pipeline(
            doc, index, lines_and_elements_tagged, processed_with_ocr
        )
    else:
        processed_with_ocr = False
        final_result = {}
        lines_and_elements_tagged = {}

    #final_result = remove_metadata_final_result(final_result)

    return final_result, class_output


def remove_metadata_final_result(final_result):
    """

    Args:
        final_result:

    Returns: The final result after removing some extra fields that may have been included for having processing
             information, but should not be in the final result structure

    """
    try:
        final_result.pop("extraInfo", None)
        return final_result
    except Exception as e:
        logger.error(traceback.format_exc())
        return final_result

def process_order_pipeline(
    doc, index, lines_and_elements_tagged, processed_with_ocr
):
    logger.info("Processing document (" + str(index) + "): " + doc)
    general_start_time = time.time()
    start_time = general_start_time
    logger.info(get_elapsed_time_message("phase 1: pre-processing", start_time))

    if not lines_and_elements_tagged:
        logging.getLogger("infra.ocr").error(
            "Error with OCR or camelot. Empty result will be generated"
        )
        final_result = {}
        return final_result, processed_with_ocr, {}

    try:

        # 5- Etiquetador de líneas
        start_time = time.time()
        parser_result = tag_with_parsers(
            lines_and_elements_tagged, extractor_config["parsers"]
        )
        logger.info(get_elapsed_time_message("phase 3: parsing", start_time))

        """
        # 7- Parser de salida
        start_time = time.time()
        final_result = OutputFormatController(
            result_desambiguator, [doc]
        ).process_result()
        """

        logger.info(get_elapsed_time_message("process document", general_start_time))

    except Exception:
        logger.debug(traceback.format_exc())

        logging.getLogger("extractor").error(
            "Error processing pdf. Empty result will be generated."
        )
        parser_result = {"value": "some error ocurred"}

    return parser_result, processed_with_ocr, lines_and_elements_tagged


def filter_elements_by_start_and_end(lines_and_elements_tagged):
    try:
        init, end = False, False
        data = lines_and_elements_tagged.get("data")
        new_data = list()
        key_init_tags = ["#inicio", "#ini"]
        key_end_tags = ["#fin"]
        for page in data:

            new_page_data_elements = list()
            for elem in page.get("elements"):

                init_line = has_element_given_body_tag(elem.get("text"), key_init_tags)
                end_line = has_element_given_body_tag(elem.get("text"), key_end_tags)
                if init_line:
                    init = True
                    new_data = list()
                    new_page_data_elements = list()
                elif end_line:
                    end = True
                    page["elements"] = new_page_data_elements
                    break
                else:
                    new_page_data_elements.append(elem)
            page["elements"] = new_page_data_elements
            new_data.append(page)
            if end_line:
                break

        lines_and_elements_tagged["data"] = new_data

        if not init and not end:
            return lines_and_elements_tagged
        else:
            for page in data:
                page["lines"] = get_lines_of_elements_ids(page)

        return lines_and_elements_tagged
    except:
        logger.debug(traceback.format_exc())
        return lines_and_elements_tagged


def get_lines_of_elements_ids(page):
    elems = page.get("elements")
    id_elems = [elem.get("orig").get("id") for elem in elems]
    lines = page.get("lines")
    new_lines = list()
    for line in lines:
        ids_line = [elem.get("id") for elem in line.get("orig")]
        if any([elem_id_line in id_elems for elem_id_line in ids_line]):
            new_lines.append(line)

    return new_lines


def get_elements_with_given_body_tag(
    elem_list: list[dict], key_tags: list
) -> list[int]:

    element_list = []

    for _elem in elem_list:
        if any([key_tag.lower() in _elem["text"].lower() for key_tag in key_tags]):
            _elem["body_tag"] = True
            element_list.append(_elem)

    return element_list


def has_element_given_body_tag(text, key_tags):
    text = text.replace("# ", "#")
    return any([key_tag.lower() in text.lower() for key_tag in key_tags])


def upload_file(con, temporal_directory, doc_name, id_pedido, directory_action):
    local_path_file = os.path.join(temporal_directory, doc_name)
    remote_path_file = id_pedido

    con.upload(local_path_file, remote_path_file, directory_action, file_name=doc_name)


def save_locally_file(_path, _name, _json):
    if not os.path.exists(_path):
        os.mkdir(_path)
    write_json(os.path.join(_path, _name), _json, indent=4)


def delete_all_data_in_folder(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.error(e)


def get_kafka_connection(config, attemps_connect, topic):
    for i in range(1, attemps_connect):
        try:
            server = str(config["HOSTNAME"]) + ":" + str(config["PORT"])
            kafka_consumer = KafkaConsumer(topic, bootstrap_servers=server)
            logger.info("Connected to Kafka")
            return kafka_consumer
        except Exception as e:
            reconnect = "Retrying again..." if i == 9 else ""
            logger.error(
                "{} - {} - Error connecting to Kafka. {}".format(
                    e.__class__.__name__, e, reconnect
                )
            )
    return


def establish_connections():
    try:
        # Conexion con filesystem
        sftp_client = SFTPConnection(system_config["sftp"])
        sftp_client.connect()
        # Conexion con elasticSearch
        elastic_client = get_elastic_client(desambiguator_config)
        # Conexión con Kafka Consumer
        kafka_client_process = get_kafka_connection(
            config=system_config["kafka"],
            attemps_connect=20,
            topic=system_config["kafka"]["topic_process"],
        )
        kafka_client_learning = get_kafka_connection(
            config=system_config["kafka"],
            attemps_connect=20,
            topic=system_config["kafka"]["topic_learning"],
        )
    except Exception as err:
        logger.error(
            "{} - {} - Error connecting to filesystem".format(
                err.__class__.__name__, err
            )
        )
        raise Exception(err)

    return sftp_client, elastic_client, kafka_client_process, kafka_client_learning


def learning_process_thread(kafka_client, postgres_client, sftp_client, elastic_client):
    for message in kafka_client:
        id_pedido = (message.value).decode()
        logger.trace(f"Nueva corrección {id_pedido}")

        try:
            # 1- Actualizar estado del pedido (POSTGRESQL)
            postgres_client.execute(
                "UPDATE pedido SET estado = 'PROCESANDO' WHERE idpedido = '"
                + id_pedido
                + "' ;"
            )
        except Exception as e:
            logger.error(
                "{} - {} - Can not be processed".format(e.__class__.__name__, e)
            )
        for doc in sftp_client.listdir(
            os.path.join(
                sftp_client.home_directory,
                sftp_client.learning_directory,
                id_pedido,
                "corregido",
            )
        ):
            try:
                # listar documentos para saber cuales procesar y descargar

                doc_path_corrected = sftp_client.download(
                    target_remote_path=os.path.join(
                        sftp_client.home_directory,
                        sftp_client.learning_directory,
                        id_pedido,
                        "corregido",
                    ),
                    target_local_path=os.path.join(
                        system_config["general"]["TEMPORARY_DIRECTORY_LEARNING"],
                        "corregido",
                    ),
                    file=doc,
                )
                doc_path_result = sftp_client.download(
                    target_remote_path=os.path.join(
                        sftp_client.home_directory,
                        sftp_client.learning_directory,
                        id_pedido,
                        "resultado",
                    ),
                    target_local_path=os.path.join(
                        system_config["general"]["TEMPORARY_DIRECTORY_LEARNING"],
                        "resultado",
                    ),
                    file=doc,
                )

                corrected = process_learning_order(
                    doc, doc_path_corrected, doc_path_result, elastic_client
                )
            except Exception as e:
                logger.error(
                    "{} - {} - Can not be processed".format(e.__class__.__name__, e)
                )

            # Borramos el fichero temporal
            delete_all_data_in_folder(
                os.path.join(
                    system_config["general"]["TEMPORARY_DIRECTORY_LEARNING"],
                    "corregido",
                )
            )
            delete_all_data_in_folder(
                os.path.join(
                    system_config["general"]["TEMPORARY_DIRECTORY_LEARNING"],
                    "resultado",
                )
            )

        try:
            # Actualizar estado del pedido (POSTGRESQL)
            postgres_client.execute(
                "UPDATE pedido SET estado = 'LISTO' WHERE idpedido = '"
                + id_pedido
                + "' ;"
            )
        except Exception as e:
            logger.error(
                "{} - {} - {} Can not be processed".format(e.__class__.__name__, e, doc)
            )


def main(path_results, log_level):
    # Log config
    if log_level is not None:
        log_config["main"]["console_level"] = log_level

    configure_logger(log_config)
    print("This is not the method to run")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="argument for generation")
    parser.add_argument("--resultsPath", type=str, required=True)
    parser.add_argument("--logLevel", type=str, required=True)
    args = parser.parse_args()

    main(args.resultsPath, args.logLevel)
