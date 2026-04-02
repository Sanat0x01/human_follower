# 🤖 Autonomous Person-Following Robot

An autonomous robotics project that uses a distributed Wi-Fi architecture to detect and track human targets in real-time. The system uses an ESP32-CAM for video streaming, processes the feed on a central computer using a MobileNet-SSD deep learning model, and issues HTTP movement commands to a NodeMCU-based robot chassis.

![Robot View](Robot%20View_screenshot_15.11.2025.png)
*Screenshot of the real-time ESP32-CAM feed with MobileNet-SSD human detection.*

## 🚀 System Architecture
This project offloads heavy deep-learning computation to a laptop/PC while keeping the robot lightweight and wireless:
* **The Eyes (ESP32-CAM):** Streams video over a local Wi-Fi network to the Python script.
* **The Brain (Python & OpenCV):** Fetches the stream, runs inference using MobileNet-SSD (Caffe), and determines if a person is in the frame.
* **The Body (NodeMCU):** Hosts a lightweight web server that receives control commands (`F` for Forward, `R` for Rotate, `S` for Stop) and drives the motor controllers.

## 🧠 Core Logic
* **Detection Threshold:** The model filters for the `person` class with a confidence threshold of >70%.
* **Tracking State:** If a human is detected, the script sends an `F` (Forward) command.
* **Searching State:** If no human is detected, the script sends an `R` (Rotate) command, causing the robot to spin in place until it finds a target.
* **Safety Protocol:** Commands are sent continuously on every frame to keep the robot's 500ms safety timer active. If the stream drops or the user quits (Ctrl+C or 'q'), an `S` (Stop) command is instantly fired to prevent runaway hardware.

## 🛠️ Technology Stack
* **Language:** Python 3
* **Computer Vision:** OpenCV (`cv2.dnn` module)
* **Networking:** `requests` library for HTTP GET commands
* **Deep Learning Model:** MobileNet-SSD (Single Shot MultiBox Detector)
* **Hardware:** ESP32-CAM, NodeMCU, Motor Drivers (e.g., L298N)

## ⚙️ How to Run

**Step 1:** Ensure the ESP32-CAM and NodeMCU are powered on and connected to the correct Wi-Fi network.

**Step 2:** Update the `NODEMCU_IP` and `stream_url` variables in the script to match your hardware's assigned IP addresses.

**Step 3:** Install the required dependencies:
```bash
pip install opencv-python numpy requests
 ```

**Step 4:** Run the controller script:
```bash
python3 robot_simulation.py
```
