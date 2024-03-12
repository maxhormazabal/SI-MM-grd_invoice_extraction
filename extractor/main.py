import argparse
import datetime
import os.path
import logging
import shutil
from extractor.common.cli.utils import read_yaml, write_json
from extractor.common.cli.logging import configure_logger, get_elapsed_time_message
from extractor.orchestrator import process_order

logger = logging.getLogger("extractor")


def get_config():
    return (
        read_yaml("extractor/common/configuration/connection_conf.yml"),
        read_yaml("extractor/common/configuration/fileprocessor_conf.yml"),
        read_yaml("extractor/common/configuration/parser_conf.yml"),
        read_yaml("extractor/common/configuration/elastic_config.yml"),
        read_yaml("extractor/common/configuration/log_config.yml"),
    )


(
    system_config,
    ocr_config,
    extractor_config,
    desambiguator_config,
    log_config,
) = get_config()


# DEJAR -- A infraestructura
def save_locally_file(
    config, num_pedido, pdf_name, pdf_path, json_result, results_path
):
    original_path = os.path.join(results_path, num_pedido, config["ORIGINAL_DIRECTORY"])
    result_path = os.path.join(results_path, num_pedido, config["RESULTS_DIRECTORY"])

    if not os.path.exists(results_path):
        os.mkdir(results_path)
    os.mkdir(os.path.join(results_path, num_pedido))
    os.mkdir(original_path)
    os.mkdir(result_path)

    result_path = os.path.join(
        result_path, pdf_name.replace(".pdf", "").replace(".PDF", "") + ".json"
    )
    move_file(original_path, pdf_name, pdf_path)

    # Guardamos el resultado
    write_json(result_path, json_result, indent=4)


def move_file(original_path, pdf_name, pdf_path):
    original_path = os.path.join(original_path, pdf_name)
    # Movemos el pdf
    shutil.move(pdf_path, original_path)


def save_locally_file_class(results_path, pdf_name, json_result, doc_path):
    result_path = os.path.join(
        results_path, pdf_name.replace(".pdf", "").replace(".PDF", "") + ".json"
    )

    # Guardamos el resultado
    write_json(result_path, json_result, indent=4)
    # shutil.move(doc_path, os.path.join(results_path, pdf_name))


# METER EN INFRAESTRUCTURA
def delete_all_data_in_folder(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.error(e)


def processing_task(path_files, path_results, class_output_path):
    num_pedido = 1
    dt = datetime.datetime.now()

    for doc in os.listdir(path_files):
        doc_path = os.path.join(path_files, doc)
        logger.trace("doc_path: " + doc_path)
        result, class_output = process_order(
            doc,
            doc_path,
            num_pedido,
            use_camelot=True,
        )

        # Guardamos el fichero en local
        save_locally_file(
            config=system_config["general"],
            num_pedido=str(dt) + "-" + str(num_pedido),
            pdf_name=doc,
            pdf_path=doc_path,
            json_result=result,
            results_path=path_results,
        )

        save_locally_file_class(
            results_path=class_output_path,
            pdf_name=doc,
            json_result=class_output,
            doc_path=doc_path,
        )

        num_pedido = num_pedido + 1



def main(path_files, path_results, class_output_path, log_level, task):
    if log_level is not None:
        log_config["main"]["console_level"] = log_level

    configure_logger(log_config)

    if task == "processing":
        processing_task(path_files, path_results, class_output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="argument for generation")
    parser.add_argument("--directoryPath", type=str, required=True)
    parser.add_argument("--resultsPath", type=str, required=True)
    parser.add_argument("--class_output_path", type=str, required=True)
    parser.add_argument("--logLevel", type=str)
    parser.add_argument("--task", type=str, required=False, default="processing")
    args = parser.parse_args()

    main(args.directoryPath, args.resultsPath, args.class_output_path, args.logLevel, args.task)
