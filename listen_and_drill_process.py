from gpiozero import Servo
from time import sleep
import paho.mqtt.client as mqtt
import keyboard
import re
import json
import time

# M1 connected to GPIO 12
# M2 connected to GPIO 13

MQTT_TOPIC = "gcs/drone_log"
MQTT_BROKER = "localhost"

MOTOR_2_PIN = 13 
manual_stop = False

# RULE FOR STARTING DRILLING
start_drilling_count = 0 # NEEDs TO GET TO 3 BEFORE DRILLING STARTS (debouncing)
# also needs to get the three within 5 seconds of each other, otherwise reset count

# KEYBOARD ESCAPE CALLBACK
def handle_key_press(event):
    # Tell this function to modify the global variable
    global manual_stop
    manual_stop = True
    print("\n[!] Key press detected! Exiting!!")

####### MQTT CALLBACKS
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT broker with code: {reason_code}")
    # We subscribe inside on_connect so that if the connection drops, 
    # it automatically re-subscribes when it reconnects.
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed to topic: {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    # msg.payload arrives as bytes, so we decode it into a standard string
    command = msg.payload.decode('utf-8').strip().lower()
    
    print(f"\n[!] Message received on {msg.topic}: {command}")

    extract_pressure(command)

    if start_drilling_count >= 3:
        print(f"[!] Pressure {pressure} bar is below threshold. Drilling hole...")
        drill_hole(userdata)  # userdata is the servo object


######## END MQTT CALLBACKS

##### STARTUP FUNCTIONS #####
def setup_motor():
    servo = Servo(MOTOR_2_PIN)
    servo.value = 0.0  # Initialize at 0 speed
    return servo

def setup_mqtt(servo):
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    # Attach the servo so callbacks can access it
    mqtt_client.user_data_set(servo)

    # Attach our callback functions
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    # connect to broker
    print("Connecting to broker...")
    mqtt_client.connect(MQTT_BROKER, 1883, 60)
    mqtt_client.loop_start()

    return mqtt_client

def setup_keyboard():
    keyboard.on_press(handle_key_press)
##### END FUNCTIONS #####


##### ACTION FUNCTIONS ####
def extract_pressure(raw_command):
    static time_last_gauge_detected = None
    pressure = None

    command = json.loads(raw_command)
    if command["action"] == "gauge detected":
        match = re.search(r"pressure: ([\d.]+) bar; image position", command["content"])
        if match:
            pressure = float(match.group(1))
            print(f"Extracted pressure: {pressure} bar")

            # if last gauge reader was less than 5 seconds ago, reset count
            if time_last_gauge_detected is None or (time.time() - time_last_gauge_detected) < 5:

                if pressure <= 2.0:
                    global start_drilling_count
                    start_drilling_count += 1
        else:
            print("No pressure detected in gauge")
        
        time_last_gauge_detected = time.time()
    return pressure

def drill_hole(servo):
    print("Sending servo command")

    # drive servo out then in
    servo.value = -0.4
    sleep(2)
    servo.value = 0.65
    sleep(1.49)

    servo.value = 0.0
    print("Stopping servo")
##### END ACTION FUNCTIONS ####


def main():
    servo = setup_motor()
    mqtt_client = setup_mqtt(servo)
    setup_keyboard()





    while not manual_stop:
        sleep(0.05)
    
    servo.value = 0.0
    servo.detach()

    # shutdown process
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

if __name__ == "__main__":
    main()
