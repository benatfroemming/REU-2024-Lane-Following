#!/usr/bin/env python3

import rospy
from std_msgs.msg import Bool, Time, Int32
from typing import Optional


MANUAL = 0
CROSSWALK = 1
INTERSECTION = 2

MODE_INT_TO_STR = {
    MANUAL: "MANUAL",
    CROSSWALK: "CROSSWALK",
    INTERSECTION: "INTERSECTION",
}

GREEN = True
RED = False

STATE_BOOL_TO_STR = {GREEN: "GREEN", RED: "RED"}

ZERO_DURATION = rospy.Duration(0)


class NonAdaptiveNorthSouthLight:
    """
    A reconfigurable traffic light node. Does not publish image topics, nor does
    it have adaptive timing capabilities.

    Only expects directions in the four primary cardinal directions.
    """

    # ---------------------------------------
    # --------- Instance Attributes ---------
    # ---------------------------------------
    run_sub: rospy.Subscriber
    mode_sub: rospy.Subscriber
    north_light_state_sub: rospy.Subscriber
    south_light_state_sub: rospy.Subscriber
    green_duration_sub: rospy.Subscriber
    red_duration_sub: rospy.Subscriber

    north_state_pub: rospy.Publisher
    south_state_pub: rospy.Publisher

    north_time_to_next_state_pub: rospy.Publisher
    south_time_to_next_state_pub: rospy.Publisher

    mode: int

    north_light_state: bool
    south_light_state: bool
    north_light_current_state: bool
    south_light_current_state: bool

    crosswalk_state: bool

    green_duration: rospy.Duration
    red_duration: rospy.Duration

    time_to_next_north_state: rospy.Duration
    time_to_next_south_state: rospy.Duration
    time_of_last_state_change: Optional[rospy.Time]

    # ---------------------------------------
    # --------- Node State Methods ----------
    # ---------------------------------------
    def __init__(self):
        rospy.init_node("non_adaptive_ns_light", anonymous=True)

        self.mode = CROSSWALK
        self.north_light_state = GREEN
        self.south_light_state = GREEN
        self.green_duration = rospy.Duration(15, 0)     # Rickey changed this to 15 GREEN
        self.red_duration = rospy.Duration(15, 0)

        self.north_light_current_state = GREEN
        self.south_light_current_state = GREEN

        self.crosswalk_state = GREEN

        self.time_to_next_north_state = rospy.Duration(-1, 0)
        self.time_to_next_south_state = rospy.Duration(-1, 0)
        self.time_of_last_state_change = None

        self.run_sub = rospy.Subscriber(
            rospy.get_param("~run_light_topic"), Time, self._run
        )

        self.mode_sub = rospy.Subscriber(
            rospy.get_param("~mode_topic"), Int32, self._set_mode
        )
        self.north_light_state_sub = rospy.Subscriber(
            rospy.get_param("~north_light_state_topic"),
            Bool,
            self._set_north_light_state,
        )
        self.south_light_state_sub = rospy.Subscriber(
            rospy.get_param("~south_light_state_topic"),
            Bool,
            self._set_south_light_state,
        )
        self.green_duration_sub = rospy.Subscriber(
            rospy.get_param("~green_duration_topic"), Int32, self._set_green_duration
        )
        self.red_duration_sub = rospy.Subscriber(
            rospy.get_param("~red_duration_topic"), Int32, self._set_red_duration
        )

        self.north_state_pub = rospy.Publisher("north/state", Bool, queue_size=1)
        self.south_state_pub = rospy.Publisher("south/state", Bool, queue_size=1)

        self.north_time_to_next_state_pub = rospy.Publisher(
            "north/time_to_next_state", Time, queue_size=1
        )
        self.south_time_to_next_state_pub = rospy.Publisher(
            "south/time_to_next_state", Time, queue_size=1
        )

    # -------------------------------------------------------
    # ------ Setters from external dynamic reconfigure ------
    # -------------------------------------------------------
    # This is so we can use dynamic reconfigure for a node running on the desktop-less
    #   RSU pi.
    def _set_mode(self, mode: Int32):
        if self.mode != mode.data:
            rospy.loginfo(
                "non_adaptive_ns_light - Mode changed from {} to {}".format(
                    MODE_INT_TO_STR[self.mode], MODE_INT_TO_STR[mode.data]
                )
            )
            rospy.loginfo(
                "non_adaptive_ns_light - North light is {}, south light is {}".format(
                    STATE_BOOL_TO_STR[self.north_light_state],
                    STATE_BOOL_TO_STR[self.south_light_state],
                )
            )
            self.north_state_pub.publish(self.north_light_state)
            self.south_state_pub.publish(self.south_light_state)
        self.mode = mode.data

    def _set_north_light_state(self, state: Bool):
        self.north_light_state = state.data

    def _set_south_light_state(self, state: Bool):
        self.south_light_state = state.data

    def _set_green_duration(self, duration: Int32):
        self.green_duration = rospy.Duration(duration.data, 0)

    def _set_red_duration(self, duration: Int32):
        self.red_duration = rospy.Duration(duration.data, 0)

    # ----------------------------
    # -------- Node Logic --------
    # ----------------------------
    def _run(self, now: Time):
        if self.mode == MANUAL:
            self._publish_manual()
            self.north_time_to_next_state_pub.publish(rospy.Duration(-10))
            self.south_time_to_next_state_pub.publish(rospy.Duration(-10))
        elif self.mode == CROSSWALK:
            self._publish_crosswalk(rospy.Time(now.data.secs, now.data.nsecs))
        elif self.mode == INTERSECTION:
            self._publish_intersection()
        else:
            rospy.logfatal(f"non_adaptive_ns_light - Illegal mode <{self.mode}>.")
            exit(1)

    def _publish_manual(self):
        if self.north_light_state is GREEN and self.north_light_current_state is RED:
            rospy.loginfo("non_adaptive_ns_light - Switching north light to green.")
            self.north_state_pub.publish(Bool(GREEN))
            self.north_light_current_state = GREEN
        if self.north_light_state is RED and self.north_light_current_state is GREEN:
            rospy.loginfo("non_adaptive_ns_light - Switching north light to red.")
            self.north_state_pub.publish(Bool(RED))
            self.north_light_current_state = RED
        if self.south_light_state is GREEN and self.south_light_current_state is RED:
            rospy.loginfo("non_adaptive_ns_light - Switching south light to green.")
            self.south_state_pub.publish(Bool(GREEN))
            self.south_light_current_state = GREEN
        if self.south_light_state is RED and self.south_light_current_state is GREEN:
            rospy.loginfo("non_adaptive_ns_light - Switching south light to red.")
            self.south_state_pub.publish(Bool(RED))
            self.south_light_current_state = RED

    def _publish_crosswalk(self, now: rospy.Time):
        if self.time_of_last_state_change is None:
            self.time_of_last_state_change = rospy.Time(now.secs, now.nsecs)
        # North and south are the same, so I picked arbitrarily here.
        if self.time_to_next_north_state <= ZERO_DURATION:
            # Checking <= for edge cases where subtracting time elapsed crosses
            #   zero seconds.
            if self.crosswalk_state == GREEN:
                rospy.loginfo("non_adaptive_ns_light - Switching crosswalk to red.")
                self.crosswalk_state = RED
                self.time_to_next_north_state = self.red_duration
                self.time_to_next_south_state = self.red_duration
                self.north_state_pub.publish(Bool(RED))
                self.south_state_pub.publish(Bool(RED))
            elif self.crosswalk_state == RED:
                rospy.loginfo("non_adaptive_ns_light - Switching crosswalk to green.")
                self.crosswalk_state = GREEN
                self.time_to_next_north_state = self.green_duration
                self.time_to_next_south_state = self.green_duration
                self.north_state_pub.publish(Bool(GREEN))
                self.south_state_pub.publish(Bool(GREEN))
            self.time_of_last_state_change = now
        else:
            time_elapsed_s = now.secs - self.time_of_last_state_change.secs
            time_elapsed_ns = now.nsecs - self.time_of_last_state_change.nsecs
            time_elapsed = rospy.Duration(time_elapsed_s, time_elapsed_ns)
            if self.crosswalk_state == GREEN:
                self.time_to_next_north_state = self.green_duration - time_elapsed
                self.time_to_next_south_state = self.green_duration - time_elapsed
            else:  # Can only be red
                self.time_to_next_north_state = self.red_duration - time_elapsed
                self.time_to_next_south_state = self.red_duration - time_elapsed
            # TODO: I'm *confident* there is a much more efficient way to calculate this.
            #       Something to do with the fact that time elapsed can be 0? I'll have to
            #       try something tomorrow. -- the man never came back
        self.north_time_to_next_state_pub.publish(self.time_to_next_north_state)
        self.south_time_to_next_state_pub.publish(self.time_to_next_south_state)

    def _publish_intersection(self):
        rospy.loginfo(
            "non_adaptive_ns_light - Intersection mode not implemented. Will try again in 10 seconds."
        )
        rospy.sleep(10)


if __name__ == "__main__":
    try:
        light = NonAdaptiveNorthSouthLight()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
