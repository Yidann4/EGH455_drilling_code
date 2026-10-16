# sudo $(which pixi) run python retract_slowly.py
from gpiozero import Servo
from time import sleep
import keyboard

MOTOR_2_PIN = 13 

# Define it once at the top
manual_stop = False

def handle_key_press(event):
    # Tell this function to modify the global variable
    global manual_stop
    manual_stop = True
    print("\n[!] Key press detected!")

def main():
    # Tell main to read the global variable
    global manual_stop
    
    servo = Servo(MOTOR_2_PIN)
    servo.value = 0.4
    
    print("Starting servo. Press ANY key to stop...")
    keyboard.on_press(handle_key_press)

    # loop until key press registered
    while not manual_stop:
        sleep(0.05)

    servo.value = 0.0
    print("Stopping servo")
    servo.detach()

if __name__ == "__main__":
    main()