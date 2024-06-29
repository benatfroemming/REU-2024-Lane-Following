#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from dynamic_reconfigure.server import Server
from line_detection.cfg import PreprocessorConfig  # packageName.cfg
import cv2 as cv
import numpy as np


class ROSImagePreprocessor:
    """
    A ROS node for preparing images for line detection and lane
    following.

    Uses dynamic reconfigure to decide which preprocessing steps
    to run.

    Preprocessing logic taken from Beñat's "advanced_dbw_follow_lane.py" code.
    """

    initial_crop_left: float
    initial_crop_right: float
    initial_crop_top: float
    initial_crop_bottom: float

    use_median_blur: bool

    filter_white: bool
    white_thresh: int

    use_canny: bool
    canny_lower_thresh: int
    canny_upper_thresh: int

    use_live_crop: bool
    live_crop_weight: float

    display_preprocessed_image: bool

    raw_img_subscriber: rospy.Subscriber
    processed_img_publisher: rospy.Publisher
    srv: Server
    # TODO: Add required live cropping subscriber

    rosimg_to_cv_bridge: CvBridge

    # ------------------------------------------------
    # ------- Internal state-related functions -------
    # ------------------------------------------------
    def __init__(self):
        # Node architecture
        rospy.init_node("line_detection_preprocessor", anonymous=True)
        self.raw_img_subscriber = rospy.Subscriber(
            rospy.get_param("~img_in_topic"), Image, self.preprocess_image
        )
        self.processed_img_publisher = rospy.Publisher(
            rospy.get_param("~img_out_topic"), Image, queue_size=1
        )
        self.srv = Server(PreprocessorConfig, self.dynamic_reconfig_callback)

        # Initially-set preprocessing parameters
        self.initial_crop_top = 0.5
        self.initial_crop_bottom = 1.0
        self.initial_crop_left = 0.0
        self.initial_crop_right = 1.0  # Crop out the top half of the image

        # TODO: Add live cropping

        self.filter_white = True
        self.white_thresh = 220

        self.use_median_blur = True

        self.use_canny = True
        self.canny_lower_thresh = 50
        self.canny_upper_thresh = 150

        self.use_live_crop = False
        self.live_crop_weight = 0.5

        self.display_preprocessed_image = False

        # Misc.
        self.rosimg_to_cv_bridge = CvBridge()

        # Begin preprocessing
        rospy.spin()

    def dynamic_reconfig_callback(self, config, _):
        self.initial_crop_top = config.initial_crop_top / 100
        self.initial_crop_bottom = config.initial_crop_bottom / 100
        self.initial_crop_left = config.initial_crop_left / 100
        self.initial_crop_right = config.initial_crop_right / 100

        self.use_median_blur = config.use_median_blur

        self.filter_white = config.filter_white
        self.white_thresh = config.white_thresh

        self.use_canny = config.use_canny
        self.canny_lower_thresh = config.canny_lower_thresh
        self.canny_upper_thresh = config.canny_upper_thresh

        self.use_live_crop = config.use_live_crop
        self.live_crop_weight = config.live_crop_weight

        self.display_preprocessed_image = config.display_preprocessed_image

        return config

    # -----------------------------------------------------
    # ----------- Image Preprocessing functions -----------
    # -----------------------------------------------------
    def preprocess_image(self, ros_image: Image):
        # Convert ROS image to OpenCV image
        try:
            cv_image = self.rosimg_to_cv_bridge.imgmsg_to_cv2(ros_image, "bgr8")
        except CvBridgeError as e:
            rospy.logerr(f"CvBridge Error: {e}")
            return

        # Initial crop
        rows, cols, _ = cv_image.shape
        cv_image = cv_image[
            int(rows * self.initial_crop_top) : int(rows * self.initial_crop_bottom),
            int(cols * self.initial_crop_left) : int(cols * self.initial_crop_right),
        ]
        rows, cols, _ = cv_image.shape

        # TODO: Add live cropping

        if self.use_median_blur:
            cv_image = cv.medianBlur(cv_image, 5)

        if self.filter_white:
            cv_image = cv.cvtColor(cv_image, cv.COLOR_BGR2GRAY)
            _, cv_image = cv.threshold(
                cv_image, self.white_thresh, 255, cv.THRESH_BINARY
            )

        if self.use_canny:
            cv_image = cv.Canny(
                cv_image, self.canny_lower_thresh, self.canny_upper_thresh
            )

        # Display and publish preprocessed image
        if self.display_preprocessed_image:
            cv.imshow("Preprocessed image", cv_image)
            cv.waitKey(1)

        try:
            self.processed_img_publisher.publish(
                self.rosimg_to_cv_bridge.cv2_to_imgmsg(cv_image)
            )
        except CvBridgeError as e:
            rospy.logerr(f"CvBridge Error: {e}")


if __name__ == "__main__":
    preprocessor = ROSImagePreprocessor()
