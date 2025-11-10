import RPi.GPIO as GPIO
import time
from signal import SIGINT, signal

def stop_fan(_num, _frame):
    # Turn the MOSFET off (pin LOW)
    GPIO.output(mosfet_pin, GPIO.LOW)
    print("MOSFET is OFF")
    exit(0)

signal(SIGINT, stop_fan)

# Set GPIO mode to BCM
GPIO.setmode(GPIO.BCM) 

# Define the GPIO pin connected to the MOSFET gate
mosfet_pin = 18

# Set up the pin as an output
GPIO.setup(mosfet_pin, GPIO.OUT)

# Turn the MOSFET on (pin HIGH)
GPIO.output(mosfet_pin, GPIO.HIGH) 
print("MOSFET is ON")

# Keep it on for a few seconds
time.sleep(60) 

stop_fan(None, None)

# Clean up GPIO on exit
GPIO.cleanup()
