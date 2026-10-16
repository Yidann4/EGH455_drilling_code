from gpiozero import Servo
from time import sleep
#import paho.mqtt.client as mqtt

MOTOR_1_PIN = 13 # M1 connected to GPIO 12

def main():
    servo = Servo(MOTOR_1_PIN)
    print("Sending servo command")
    servo.value = -0.4
    sleep(2)
    servo.value = 0.65
    sleep(2)
    servo.value = 0.0
    print("Stopping servo")
    servo.detach()

if __name__ == "__main__":
    main()
