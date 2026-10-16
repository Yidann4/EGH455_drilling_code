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
DRILL_TRIGGER_COUNT = 2 # number of sub 2.0 bar readings needed before drilling starts (debouncing)
GAUGE_WINDOW_SECONDS = 11 # readings must be within this many seconds of each other, otherwise reset count
COOLDOWN_SECONDS = 10 # ignore MQTT messages for this long after a drill finishes

start_drilling_count = 0
time_last_gauge_detected = None
cooldown_until = 0.0 # time.time() value before which MQTT messages are ignored

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
    global cooldown_until

    # ignore everything during the cooldown after a drill
    if time.time() < cooldown_until:
        return

    # msg.payload arrives as bytes, so we decode it into a standard string
    command = msg.payload.decode('utf-8').strip().lower()

    # print(f"\n[!] Message received on {msg.topic}: {command}")

    # a malformed message must not kill the MQTT thread
    try:
        pressure = extract_pressure(command)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        print(f"[!] Ignoring bad message: {e}")
        return

    if start_drilling_count >= DRILL_TRIGGER_COUNT:
        print(f"[!] Pressure {pressure} bar is below threshold. Drilling hole...")
        drill_hole(userdata)  # userdata is the servo object
        reset_trigger_state()
        # messages that arrived while drilling will land inside this window and be ignored
        cooldown_until = time.time() + COOLDOWN_SECONDS
        print(f"Drill complete. Ignoring MQTT for {COOLDOWN_SECONDS}s...")


######## END MQTT CALLBACKS

##### STARTUP FUNCTIONS #####
def setup_motor():
    servo = Servo(MOTOR_2_PIN)
    servo.detach() # to ensure no movement
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
    global time_last_gauge_detected
    global start_drilling_count

    pressure = None

    command = json.loads(raw_command)
    if command["action"] == "gauge detected":
        match = re.search(r"pressure: ([\d.]+) bar; image position", command["content"])
        if match:
            pressure = float(match.group(1))
            print(f"Extracted pressure: {pressure} bar")

            # if last gauge reading was too long ago, start the count over
            if time_last_gauge_detected is not None and (time.time() - time_last_gauge_detected) >= GAUGE_WINDOW_SECONDS:
                start_drilling_count = 0

            if pressure <= 2.0:
                start_drilling_count += 1
            else:
                start_drilling_count = 0
        else:
            start_drilling_count = 0
            print("No pressure detected in gauge")

        time_last_gauge_detected = time.time()
    return pressure

def reset_trigger_state():
    global start_drilling_count
    global time_last_gauge_detected
    start_drilling_count = 0
    time_last_gauge_detected = None

def drill_hole(servo):
    print("Sending servo command")

    try:
        # drive servo out then in
        servo.value = -0.4
        sleep(2)
        servo.value = 0.65
        sleep(1.49)
    finally:
        # always stop sending pulses, even if something goes wrong mid-move
        servo.detach()
        print("Stopping servo")

##### END ACTION FUNCTIONS ####


def main():
    servo = setup_motor()
    mqtt_client = setup_mqtt(servo)
    setup_keyboard()

    while not manual_stop:
        sleep(0.05)

    servo.detach()

    # shutdown process
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

if __name__ == "__main__":
    main()
