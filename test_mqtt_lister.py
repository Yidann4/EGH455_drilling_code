import paho.mqtt.client as mqtt
from time import sleep

TOPIC = "gcs/drone_log"
MQTT_BROKER = "localhost"


# example message: {"action": "gauge detected", "content": "pressure: 2.91 bar; image position (963, 531) px; frame 13809."}


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT broker with code: {reason_code}")
    # We subscribe inside on_connect so that if the connection drops, 
    # it automatically re-subscribes when it reconnects.
    client.subscribe(TOPIC)
    print(f"Subscribed to topic: {TOPIC}")

def on_message(client, userdata, msg):
    # msg.payload arrives as bytes, so we decode it into a standard string
    command = msg.payload.decode('utf-8').strip().lower()
    
    print(f"\n[!] Message received on {msg.topic}: {command}")
    
    # You can put your logic here
    if command == "stop":
        print("Executing stop command...")
        # manual_stop = True
    elif command == "extend":
        print("Extending drill...")

def main():
    # Setup the MQTT client (VERSION2 is required for the latest paho-mqtt library)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    # Attach our callback functions
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the broker
    print("Connecting to broker...")
    client.connect(MQTT_BROKER, 1883, 60)

    # Start the network loop in a background thread
    client.loop_start()
    
    print("Main program is running. Waiting for messages...")
    
    try:
        # Your main loop can do other things while MQTT listens in the background
        while True:
            sleep(0.1)
    except KeyboardInterrupt:
        # Cleanly disconnect if you press Ctrl+C
        print("\nExiting program...")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()