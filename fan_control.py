import RPi.GPIO as GPIO
import time

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

# Turn the MOSFET off (pin LOW)
GPIO.output(mosfet_pin, GPIO.LOW)
print("MOSFET is OFF")

# Clean up GPIO on exit
GPIO.cleanup()
