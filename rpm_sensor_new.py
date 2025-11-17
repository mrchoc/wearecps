import RPi.GPIO as GPIO
import time

# --- CONFIGURATION ---
SENSOR_PIN = 17     # GPIO pin connected to TCRT5000 output
NUM_BLADES = 2

# formula = 1 / (interval * blades) * 60
# assuming interval is in seconds
RECIPROCAL_COEFFICIENT = 60 / NUM_BLADES

# --- SETUP ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Measuring RPM... Press Ctrl+C to stop.")

start_time = time.time()

try:
    while True:
        GPIO.wait_for_edge(SENSOR_PIN, GPIO.RISING)

        end_time = time.time()

        rpm = RECIPROCAL_COEFFICIENT / (end_time - start_time)

        start_time = time.time()

        print(f"Instantaneous RPM: {rpm:.2f}")

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    GPIO.cleanup()
