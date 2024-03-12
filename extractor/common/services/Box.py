import logging
from math import dist

logger = logging.getLogger("service.box")

"""
    Graphical definition of Box and its parameters:

           #
      y1 - #        ############################################
         | #        #                                          #
         | #        #                                          #
    height #        #                   BOX                    #
         | #        #                                          #
         | #        #                                          #
      y0 - #        ############################################
           #
           #############################################################
                     |<-----------------width------------------>|
                    x0                                         x1
"""


class Box:
    def __init__(self, content):
        self.content = content
        self.text = content["text"]
        self.x0 = content["x0"]
        self.x1 = content["x1"]
        self.y0 = content["y0"]
        self.y1 = content["y1"]
        self.centerX, self.centerY = self.get_center()
        self.width, self.height = self.get_dimensions()

    def get_center(self):
        centerX = self.x1 - (self.x1 - self.x0) / 2
        centerY = self.y1 - (self.y1 - self.y0) / 2
        return centerX, centerY

    def get_dimensions(self):
        width = self.x1 - self.x0
        height = self.y1 - self.y0
        return width, height


def distance_boxes(box1, box2):
    """
    :param box1:
    :param box2:
    :return: The distance between the centers of both boxes
    """
    distance = dist([box1.centerX, box1.centerY], [box2.centerX, box2.centerY])
    return distance


def horizontal_distance_boxes(box1, box2, scope="center", abs_value=False):
    """
    :param box1:
    :param box2:
    :param scope: The scope from which calculates the distances. If 'center', the distance between centers. If 'left' or
                  'right', the distance between both left or both right edges of the boxes.
    :param abs_value: If true, the distance is an absolute value. If False, the distance can be positive or negative
    :return: The horizontal component of the distance between both boxes.
    """
    if scope not in ["center", "left", "right"]:
        logger.warning(
            "{} is not a valid scope for horizontal_distance_boxes(). Center scope will be used as default".format(
                scope
            )
        )
        scope = "center"

    if scope == "center":
        distance = box2.centerX - box1.centerX
    if scope == "left":
        distance = box2.x0 - box1.x0
    if scope == "right":
        distance = box2.x1 - box1.x1

    if abs_value:
        distance = abs(distance)
    return distance


def vertical_distance_boxes(box1, box2, scope="center", abs_value=False):
    """
    :param box1:
    :param box2:
    :param scope: The scope from which calculates the distances. If 'center', the distance between centers. If 'top' or
              'bottom', the distance between both top or both bottom edges of the boxes.
    :param abs_value: If true, the distance is an absolute value. If False, the distance can be positive or negative
    :return: The vertical component of the distances of the centers.
    """

    if scope not in ["center", "top", "bottom"]:
        logger.warning(
            "{} is not a valid scope for vertical_distance_boxes(). Center scope will be used as default".format(
                scope
            )
        )
        scope = "center"

    if scope == "center":
        distance = box2.centerY - box1.centerY
    if scope == "top":
        distance = box2.y1 - box1.y1
    if scope == "bottom":
        distance = box2.y0 - box1.y0

    if abs_value:
        distance = abs(distance)
    return distance


def boxes_same_line(box1, box2, threshold=None):
    """
    :param box1:
    :param box2:
    :param threshold: below this value of distance, boxes are considered to be in the same line
    :return: True if the boxes are in the same line
    """
    if threshold is None:
        threshold = max(box1.height / 3, box2.height / 3)
    vdist = vertical_distance_boxes(box1, box2, scope="center", abs_value=False)
    return True if abs(vdist) < threshold else False


def boxes_same_column(box1, box2, threshold=5):
    """
    :param box1:
    :param box2:
    :param threshold: below this value of distance between their left edges, boxes are considered to be in the same column
    :return: True if the boxes are in the same column
    """
    hdist = horizontal_distance_boxes(box1, box2, scope="left", abs_value=False)
    return True if abs(hdist) < threshold else False


def horizontal_distance_boxes_minimum(box1, box2, abs_value=False):
    """
    :param box1:
    :param box2:
    :return: Minimum horizontal distance between edges of the boxes. Maximum absolute value but result is not absolute value. If their are exactly next to each other it should be 0.
    """
    distance0 = box2.x0 - box1.x1
    distance1 = box2.x1 - box1.x0
    distance2 = box2.x0 - box1.x0
    distance3 = box2.x1 - box1.x1
    min_distance = min([distance1, distance0, distance2, distance3], key=abs)
    if abs_value:
        min_distance = abs(min_distance)
    return min_distance


def vertical_distance_boxes_minimum(box1, box2, abs_value=False):
    """
    :param box1:
    :param box2:
    :return: Minimum vertical distance between edges of the boxes. In absolute value. If their are exactly next to each other it should be 0.
    """
    distance0 = box2.y0 - box1.y1
    distance1 = box2.y1 - box1.y0
    distance2 = box2.y0 - box1.y0
    distance3 = box2.y1 - box1.y1
    min_distance = min([distance0, distance1, distance2, distance3], key=abs)
    if abs_value:
        min_distance = abs(min_distance)
    return min_distance


def doOverlap(box0, box1):
    """
    :param box0:
    :param box1:
    :return: return True if there is overlapping between boxes. Else False
    """
    return doVerticalOverlap(box0, box1) and doHorizontalOverlap(box0, box1)


def doVerticalOverlap(box0, box1):
    """
    :param box0:
    :param box1:
    :return: return True if there is vertical overlapping between boxes. Else False
    """
    # If one rectangle is above other
    return not (box0.y0 > box1.y1 or box1.y0 > box0.y1)


def doHorizontalOverlap(box0, box1):
    """
    :param box0:
    :param box1:
    :return: return True if there is horizontal overlapping between boxes. Else False
    """

    # If one rectangle is on left side of other
    return not (box0.x0 > box1.x1 or box1.x0 > box0.x1)


def minimum_minimum_horizontal_or_vertical_distance_boxes(box1, box2):
    return min(
        abs(vertical_distance_boxes_minimum(box1, box2)),
        abs(horizontal_distance_boxes_minimum(box1, box2)),
    )


def maximum_minimum_horizontal_or_vertical_distance_boxes(box1, box2):
    vertical_dist = abs(vertical_distance_boxes_minimum(box1, box2))
    horizontal_dist = abs(horizontal_distance_boxes_minimum(box1, box2))
    values = [vertical_dist, horizontal_dist]
    max_value = max(values)
    max_index = values.index(max_value)
    index_names = ["vertical", "horizontal"]
    return max_value, index_names[max_index]
