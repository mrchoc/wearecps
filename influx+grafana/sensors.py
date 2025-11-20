import time
import smbus2
import bme280
import RPi.GPIO as GPIO
import max6675
from ina219 import INA219
from ina219 import DeviceRangeError
from smbus2 import SMBus
from mlx90614 import MLX90614
import pigpio

GPIO.setmode(GPIO.BCM)

# current sensor
SHUNT_OHMS = 0.1
ina = INA219(SHUNT_OHMS, busnum=1)
ina.configure()

# rpm sensor
pulse_count = 0
last_count = 0
last_time = time.time()
rpm_counts = []
start_time = time.time()
def pulse_callback(channel):
    global pulse_count
    pulse_count += 1
SENSOR_PIN = 17
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(SENSOR_PIN, GPIO.FALLING, callback=pulse_callback, bouncetime=5)

# hot side temp
cs = 10
sck = 11
so = 9

max6675.set_pin(cs, sck, so, 1)

def air_sensor():
    # BME280 sensor address (default address)
    address = 0x76

    # Initialize I2C bus
    bus = smbus2.SMBus(1)

    # Load calibration parameters
    calibration_params = bme280.load_calibration_params(bus, address)

    def celsius_to_fahrenheit(celsius):
        return (celsius * 9/5) + 32

    try:
        # Read sensor data
        data = bme280.sample(bus, address, calibration_params)

        # Extract temperature, pressure, and humidity
        temperature_celsius = data.temperature
        pressure = data.pressure
        humidity = data.humidity

        # Convert temperr hnt(temperature_celsius)
        temperature_fahrenheit = celsius_to_fahrenheit(temperature_celsius)
        
        return "{:.2f}".format(temperature_celsius)

    except Exception as e:
        print('An unexpected error occurred:', str(e))

def current_sensor_voltage():
    try:
        return 11 - ina.voltage()
    except DeviceRangeError as e:
        # Current out of device range with specified shunt resistor
        print(e)

def current_sensor_power():
    try:
        return ina.power()
    except DeviceRangeError as e:
        # Current out of device range with specified shunt resistor
        print(e)

def ir_temp():
    bus = SMBus(1)
    sensor = MLX90614(bus, address=0x5A)

    return sensor.get_obj_temp()

def cold_side_temp(sensor):
    temperature_in_celsius = sensor.get_temperature()

    return temperature_in_celsius

def hot_side_temp():
    temp = max6675.read_temp(cs)
    return temp

def rpm_sensor():
    MARKS_PER_REV = 5   # number of reflective marks on the rotating disk

    global last_count
    global last_time
    pulses = pulse_count - last_count
    last_count = pulse_count
    if len(rpm_counts) >= 60:
        rpm_counts.pop(0)
    rpm_counts.append(pulses/MARKS_PER_REV)

    current_time = time.time()
    seconds = current_time - last_time
    rps = pulses / seconds
    last_time = current_time

    # print(f"Current RPM: {sum(rpm_counts)/len(rpm_counts)*60:.2f}")
    # print(f"Average RPM: {rps*60:.2f}")
    # print(f"Average RPS: {rps:.2f}")

    return rps * 60 / MARKS_PER_REV

INSTANT_RPM_PIN = 23
GPIO.setup(INSTANT_RPM_PIN , GPIO.IN, pull_up_down=GPIO.PUD_UP)

# formula = 1 / (interval * blades) * 60
# assuming interval is in seconds
NUM_BLADES = 5
RECIPROCAL_COEFFICIENT = 60 / NUM_BLADES

def instant_rpm():
    start_time = time.time()
    while True:
        GPIO.wait_for_edge(INSTANT_RPM_PIN, GPIO.RISING)

        end_time = time.time()

        rpm = RECIPROCAL_COEFFICIENT / (end_time - start_time)

        start_time = time.time()

        yield rpm

FAN_GPIO = 18
GPIO.setup(FAN_GPIO, GPIO.OUT)

def set_fan_state(boolean):
    GPIO.output(FAN_GPIO, GPIO.HIGH if boolean else GPIO.LOW)
    return boolean