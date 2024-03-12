import json
import logging
from .custom_exceptions import ParserFormatterError


logger = logging.getLogger("format.parser")


def _read_ndjson(filepath: str):
    """Reads and ndjson and returns the list of dicts

    Args:
      filepath: str to the file

    Returns:
      a list of dicts with the information of the file

    """

    data_list = []

    with open(filepath, "r") as f_in:
        for line in f_in:
            _json = json.loads(line)
            data_list.append(_json)

    return data_list


def read_files_list(
    elements_file_list: list[str], lines_file_list: list[str]
) -> list[dict]:
    """Reads ndjson files and stores them in a list of dicts

    It joins elements and lines in one object
    The number of elements and lines should be the same

    Args:
      elements_file_list: list of paths to files with elements
      lines_file_list: list of path to files with lines

    Returns:
      a list of dicts with the elements and lines joined

    """

    data_list = []

    if elements_file_list is not None and lines_file_list is not None:

        # picking first element as source
        source = elements_file_list[0]

        if len(elements_file_list) != len(lines_file_list):
            raise ParserFormatterError(
                "Same number of elements and lines files should be provided"
            )

        for idx in range(len(elements_file_list)):
            _path_elems = elements_file_list[idx]
            _path_lines = lines_file_list[idx]

            _elems_list = _read_ndjson(_path_elems)
            _lines_list = _read_ndjson(_path_lines)

            data_list.append(
                {
                    "source": source,
                    "page": idx,
                    "elements": _elems_list,
                    "lines": _lines_list,
                }
            )

    elif elements_file_list is not None:
        for idx in range(len(elements_file_list)):
            _path_elems = elements_file_list[idx]
            _elems_list = _read_ndjson(_path_elems)

            data_list.append(
                {"source": source, "page": idx, "elements": _elems_list, "lines": []}
            )

    elif lines_file_list is not None:
        for idx in range(len(lines_file_list)):
            _path_lines = lines_file_list[idx]
            _lines_list = _read_ndjson(_path_lines)

            data_list.append(
                {"source": source, "page": idx, "elements": [], "lines": _lines_list}
            )

    else:
        raise ParserFormatterError("No valid file provided")

    return data_list


def dump_io_data(data_list: list[dict], output_file: str):
    """Dump information to the output file

    Args:
      data_list: list of dicts with information from each source
      output_file: output file to save the structure

    """

    _json = {"data": data_list, "annotations": {}}

    with open(output_file, "w+") as f_out:
        f_out.write("{}\n".format(json.dumps(_json, indent=4, sort_keys=True)))
