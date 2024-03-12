from abc import ABC, abstractmethod


class BaseController(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def process_result(self):
        pass

    @abstractmethod
    def process_input(self):
        pass

    def check_lines_and_elements(self):

        for idx, _datum in enumerate(self.input_doc["data"]):
            if "elements" not in _datum or "lines" not in _datum:
                raise Exception("Every document should contain lines and elements")

        # podemos introducirlo en BaseController y pasarle el TAG simplemente

    def get_elements_with_a_given_tag(
        self, elem_list: list[dict], tag: str
    ) -> list[int]:
        """Returns the list of ids of elements with a given tag detection

        Args:
           elem_list: list of elements of a document
           tag: the tag you want to find

        Returns:
          the list of ids of the elements with the given tag

        """

        element_list = []

        for _elem in elem_list:
            if tag in _elem["labels"]:
                # id_element_list.append(_elem["orig"]["id"])
                element_list.append(_elem)

        return element_list

    def get_elements_with_a_given_list_of_tags(
        self, elem_list: list[dict], tags: list
    ) -> list[int]:
        """Returns the list of ids of elements with given tags detection

        Args:
           elem_list: list of elements of a document
           tag: a list of the tags you want to find

        Returns:
          the list of ids of the elements with the given tags

        """

        element_list = []

        for _elem in elem_list:
            if any([tag in _elem["labels"] for tag in tags]):
                # id_element_list.append(_elem["orig"]["id"])
                element_list.append(_elem)

        return element_list

    def get_line_idx_with_a_given_elements(
        self, lines_list: list[dict], id_element_list: list[dict]
    ) -> list[int]:
        """Get the ids of the lines with note elements

        Args:
          lines_list: list of lines of a document
          id_element_list: list of ids of elements with note annotations

        """

        id_lines_list = []

        for idx, _line in enumerate(lines_list):
            for _elem in _line["orig"]:
                if _elem["id"] in id_element_list:
                    id_lines_list.append(idx)

        return id_lines_list

    def get_all_elements_with_a_given_tag(
        self, data_list: list[dict], tag: str
    ) -> list[dict]:

        element_list = []
        for _page in data_list:
            for _elem in _page["elements"]:
                if tag in _elem["labels"]:
                    element_list.append(_elem)

        return element_list

    def get_page_label_annotations(
        self, annotations: list[dict], page: str, label: str
    ):
        """
        Filters the input annotations from the specified page and label
        Parameters
        ----------
        annotations:
        page
        label

        Returns a list of the filtered annotations
        -------

        """
        return [x for x in annotations[label] if x["page"] == page]

    def get_annotations_in_page(self, annotations, label, page=None):
        """
        Filters the input annotations from the specified page and label
        Parameters
        ----------
        annotations:
        page
        label

        Returns a list of the filtered annotations
        -------

        """
        if label not in annotations:
            return []
        if page:
            return [x for x in annotations[label] if x["page"] == page]
        else:
            return [x for x in annotations[label]]

    def transform_element_to_annotation(self, elements, page, source):
        annotations = list()
        for element in elements:
            annotation = {
                "text": element["text"],
                "source": source,
                "page": page,
                "elements": [element["orig"]["id"]],
            }
            annotations.append(annotation)
        return annotations

    def get_desambiguated_data(self, desambiguated, label):
        return desambiguated.get(label)

    def get_body_output_format(self, text, score=None, raw_elements=None):
        if not raw_elements:
            raw_elements = [self.get_raw_element(None, None, None, None, None)]
        body = {
            "text": text,
            "score": score,
            "validation": None,
            "raw": raw_elements,
        }
        return body

    def get_raw_element(self, sourceFile, page, regionCoords, line, rawText):
        if not regionCoords:
            regionCoords = [
                {"x": None, "y": None},
                {"x": None, "y": None},
                {"x": None, "y": None},
                {"x": None, "y": None},
            ]
        raw_elem = {
            "sourceFile": sourceFile,
            "page": page,
            "regionCoords": regionCoords,
            "line": line,
            "rawText": rawText,
        }
        return raw_elem

    def get_coords_of_elements(self, elements_ids, data_pages, page_num):

        element_coords = []
        for page in data_pages:
            if page["page"] == page_num:
                for _elem in page["elements"]:
                    if _elem["orig"]["id"] in elements_ids:
                        orig = _elem["orig"]
                        output = [
                            {"x": orig["x0"], "y": orig["y1"]},
                            {"x": orig["x0"], "y": orig["y0"]},
                            {"x": orig["x1"], "y": orig["y1"]},
                            {"x": orig["x1"], "y": orig["y0"]},
                        ]
                        element_coords.append(output)

        return element_coords

    def get_raws_of_elements(self, elements_ids, data_pages, page_num, sourceFile):

        element_raws = []

        for page in data_pages:
            if page.get("page") == page_num:
                for _elem in page.get("elements", []):
                    if _elem.get("orig").get("id") in elements_ids:
                        orig = _elem.get("orig")
                        coords = [
                            {"x": orig.get("x0"), "y": orig.get("y1")},
                            {"x": orig.get("x0"), "y": orig.get("y0")},
                            {"x": orig.get("x1"), "y": orig.get("y1")},
                            {"x": orig.get("x1"), "y": orig.get("y0")},
                        ]
                        output = {
                            "sourceFile": sourceFile,
                            "page": page_num,
                            "regionCoords": coords,
                            "line": None,
                            "rawText": orig.get("text"),
                        }
                        element_raws.append(output)

        return element_raws

    def get_desamibiguated_client_data(self):

        client = None
        client_group = None
        country = None

        minimum_score_acceptable_client_data = 0.5
        minimum_score_acceptable_address_data = 0.5

        try:
            clientScore = (
                self.input_doc.get("desambiguated")
                .get("client")
                .get("infoCliente")
                .get("nombreCliente")
                .get("score")
            )
            if clientScore and clientScore >= minimum_score_acceptable_client_data:
                client = (
                    self.input_doc.get("desambiguated")
                    .get("client")
                    .get("infoCliente")
                    .get("nombreCliente")
                    .get("text")
                )
        except Exception as e:
            pass

        try:
            clientGroupScore = (
                self.input_doc.get("desambiguated").get("clientGroup").get("score")
            )
            if (
                clientGroupScore
                and clientGroupScore >= minimum_score_acceptable_client_data
            ):
                client_group = (
                    self.input_doc.get("desambiguated")
                    .get("clientGroup")
                    .get("clientGroup")
                )
        except Exception as e:
            pass

        try:
            addressScore = (
                self.input_doc.get("desambiguated")
                .get("deliveryaddress")
                .get("infoDireccionEntrega")
                .get("paisEntrega")
                .get("score")
            )
            if addressScore and addressScore >= minimum_score_acceptable_address_data:
                country = (
                    self.input_doc.get("desambiguated")
                    .get("deliveryaddress")
                    .get("infoDireccionEntrega")
                    .get("paisEntrega")
                    .get("text")
                )
        except Exception as e:
            pass

        return client, client_group, country

    def _get_element_with_a_given_id(self, elements, id) -> list[int]:

        for element in elements:
            if element["orig"]["id"] == id:
                return element
        return None

    def safeget(self, dct, *keys):
        for key in keys:
            try:
                dct = dct[key]
            except KeyError:
                return None
        return dct
