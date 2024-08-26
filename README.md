# V2X REU 2024 Repository

![image](https://github.com/user-attachments/assets/0280b4e2-2846-422b-a410-7883fd8d00ef)

Research Team:

- Marcial Machado
- Michael Evans
- Rickey Johnson
- Beñat Froemming-Aldanondo
- Tatiana Rastoskueva
- Luis Escamilla
- Anna Vadella

Graduate Assistants:

- Devson Butani
- Milan Jostes
- Ryan Kaddis

Principal Investigators:

- Dr. Chan-Jin Chung
- Dr. Joshua Siegel

## Testing and Launching

Ubuntu 20.04 "Focal Fossa" is recommended. ROS Noetic should be installed.

The following Python packages are required:

- Rospy
- Scikit learn
- OpenCV

### Launch configurations

The launch file used for testing the lane following algorithms on the simulator or the ACTor vehicles is `follow_lane_one_car.launch`. These are the arguments available to change (those with \*stars *must* be set manually):

`follow_lane_one_car.launch`:
- `vehicle_namespace` (default: "robot1"): "robot1", "actor1", "actor2": This is the vehicle being run (the first option is to run Gazelle Sim).
- `preprocessor` (default: "easy_birdseye"): "easy_birdseye", "full", "passthrough", "crop_only": The initial image preprocessor.
- `lane_detector` (default: "dbscan"): "dbscan", "kmeans", "birdsdbs", "birdseye", "deeplsd", "kmeans", "largest_contour": The lane detection algorithm. **Note:** the "birds-" family of lane detectors *requires* the "passthrough" preprocessor.
- \*`lane_name` (default: "northbound"): "northbound", "eastbound": the H lot lane the car is driving in. The inner lane is northbound.
