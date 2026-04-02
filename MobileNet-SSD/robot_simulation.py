import cv2
import numpy as np
import time
import requests
import sys

# --- Configuration ---
CONFIDENCE_THRESHOLD = 0.7

# --- Model Setup ---
prototxt_path = "deploy.prototxt"
model_path = "mobilenet_iter_73000.caffemodel"
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]

# --- NodeMCU (Robot) Web Server URL ---
# !!! IP UPDATE HO GAYA HAI (AAPKE INPUT KE ANUSAAR) !!!
NODEMCU_IP = "http://10.106.22.115"
CONTROL_URL = f"{NODEMCU_IP}/control"

# --- ESP32-CAM Stream URL ---
# !!! IP UPDATE HO GAYA HAI (AAPKE INPUT KE ANUSAAR) !!!
stream_url = "http://10.106.22.125:81/stream" 

# --- Helper function for clean terminal output ---
def print_status(message):
    # Clears the entire line and prints the new message
    # The ' ' padding ensures old text is overwritten
    sys.stdout.write('\r' + message.ljust(80) + '\r')
    sys.stdout.flush()

def print_log(message):
    # Prints a permanent log message on a new line
    sys.stdout.write('\n' + message + '\n')
    sys.stdout.flush()

# --- 1. Load AI Model ---
print("-> Loading AI model...")
try:
    net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
    print_log("-> Model loaded successfully.")
    print(f"-> Robot Controller IP: {NODEMCU_IP}")
except cv2.error as e:
    print_log(f"!!! FATAL ERROR: Could not load model files.")
    print_log(f"    Check if '{prototxt_path}' and '{model_path}' are in the correct folder.")
    print_log(f"    OpenCV Error: {e}")
    exit()


# --- 2. Connect to ESP32-CAM Stream ---
print(f"-> Connecting to ESP32-CAM at {stream_url}...")
cap = cv2.VideoCapture(stream_url)

if not cap.isOpened():
    print_log("\n!!! FATAL ERROR: Could not connect to ESP32-CAM stream.")
    print_log(f"    1. Check if the ESP32-CAM is powered on.")
    print_log(f"    2. Check if your laptop is on the same Wi-Fi ('Sanat').")
    print_log(f"    3. Test if this URL works in your browser: {stream_url}")
    exit()

print_log("-> Stream connected! Starting detection loop...")
time.sleep(0.5) # Reduced sleep time as requested

# --- 3. Main Program Logic ---
while True:
    try:
        # Get an image from the webcam.
        ret, frame = cap.read()
        if not ret: 
            print_log("\n!!! ERROR: Stream disconnected. Reconnecting...")
            cap.release()
            cap = cv2.VideoCapture(stream_url)
            # Send a STOP command if the stream fails
            try:
                requests.get(f"{CONTROL_URL}?command=S", timeout=0.1)
            except: pass
            time.sleep(0.5) # Reduced sleep time
            continue

        (h, w) = frame.shape[:2]
        # Prepare the image to be fed into the AI.
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)

        # Find all objects in the image.
        net.setInput(blob)
        detections = net.forward()
        person_found = False

        # Check if any of the detected objects is a person.
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > CONFIDENCE_THRESHOLD:
                idx = int(detections[0, 0, i, 1])
                if CLASSES[idx] == "person":
                    person_found = True
                    # Draw a green box on the video feed.
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
                    break # Stop after finding the first person.

        # --- Tell the REAL robot what to do ---
        command_to_send = ""
        status_message = ""
        
        # --- LOGIC AUR COMMENTS AB 100% SAHI HAIN ---
        if person_found:
            # Insaan dikha -> 'F' (Forward) bhejo
            status_message = "STATUS: Human detected! Sending 'Forward' (F) command."
            command_to_send = "F"
        else:
            # Insaan nahi dikha -> 'R' (Rotate) bhejo
            status_message = "STATUS: Searching... (Sending 'Rotate' (R) command.)"
            command_to_send = "R"
            
        # --- THIS IS THE NEW CLEAN TERMINAL OUTPUT ---
        print_status(status_message)

        # --- "SMART" SPAM BLOCKER REMOVED ---
        # Ab yeh har frame par command bhejega
        # Isse robot ka 500ms ka safety timer reset hota rahega
        try:
            # Send the command as a web request
            requests.get(f"{CONTROL_URL}?command={command_to_send}", timeout=0.1)
        except requests.exceptions.RequestException as e:
            # This happens if the robot is off or Wi-Fi is down
            print_log(f"\n!!! WARNING: Failed to send command to robot. (Check robot power?)")

        # Show the webcam video on your screen.
        cv2.imshow("Robot View (Press 'q' to quit)", frame)
        key = cv2.waitKey(1) & 0xFF

        # Press 'q' on your keyboard to quit the program.
        if key == ord("q"):
            print_log("\n-> 'q' pressed. Sending STOP command...")
            try:
                requests.get(f"{CONTROL_URL}?command=S", timeout=1) # Stop on quit
            except: pass
            break
            
    except KeyboardInterrupt:
        # Handle Ctrl+C
        print_log("\n-> Ctrl+C pressed. Sending STOP command...")
        try:
            requests.get(f"{CONTROL_URL}?command=S", timeout=1)
        except: pass
        break

# --- Cleanup ---
print_log("-> Shutting down. Sending final STOP command.")
try:
    requests.get(f"{CONTROL_URL}?command=S", timeout=1) # Final stop
except: pass

cap.release()
cv2.destroyAllWindows()
print_log("-> Script finished. Goodbye.")
