import RPi.GPIO as GPIO
import time

# --- CONFIGURATION ---
SENSOR_PIN = 17     # GPIO pin connected to TCRT5000 output
MARKS_PER_REV = 1   # number of reflective marks on the rotating disk
UPDATE_INTERVAL = 1 # seconds between RPM calculations

# --- SETUP ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

pulse_count = 0

def pulse_callback(channel):
    global pulse_count
    pulse_count += 1

# Detect falling edge (change to RISING if opposite logic)
GPIO.add_event_detect(SENSOR_PIN, GPIO.FALLING, callback=pulse_callback, bouncetime=5)

print("Measuring RPM... Press Ctrl+C to stop.")

rpm_counts = []

start_time = time.time()

try:
    while True:
        start_count = pulse_count
        time.sleep(UPDATE_INTERVAL)
        end_count = pulse_count

        pulses = end_count - start_count
        if len(rpm_counts) >= 60:
            rpm_counts.pop(0)
        rpm_counts.append(pulses/MARKS_PER_REV)

        current_time = time.time()
        seconds_since_start = current_time - start_time
        rps = pulse_count / seconds_since_start

        print(f"Current RPM: {sum(rpm_counts)/len(rpm_counts)*60:.2f}")
        print(f"Average RPM: {rps*60:.2f}")
        print(f"Average RPS: {rps:.2f}")

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    GPIO.cleanup()
