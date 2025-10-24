# dummystream.py - TEG Rotor IoT System Data Simulator
import time
import random
import math
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
#IR
from smbus2 import SMBus
from mlx90614 import MLX90614
#current
from ina219 import INA219
from ina219 import DeviceRangeError
#air
import smbus2
import bme280
#cold side
from ds18b20 import DS18B20
#rpm
import RPi.GPIO as GPIO
#hot side
import max6675



import os

# InfluxDB Configuration
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', 'your-token-here')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'myorg')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'teg_rotor')

# Simulation parameters
RPM_BASELINE = 1200  # RPM threshold for fan activation
RPM_OPTIMAL = 1500   # Target RPM when fan is active

#for current sensor
SHUNT_OHMS = 0.1

#for air sensor temp unit conversion
def celsius_to_fahrenheit(c):
    return (c * 9/5) + 32



class TEGRotorSimulator:
    def __init__(self):
        self.client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        
        # ---- Sensor setup ---- #
        # IR sensor
        self.bus = SMBus(1)
        self.ir_sensor = MLX90614(self.bus, address=0x5A)

        # Current sensor
        self.current_sensor = INA219(SHUNT_OHMS, busnum=1)
        self.current_sensor.configure()

        # Air sensor
        self.bus = smbus2.SMBus(1)
        self.bme280_address = 0x76
        self.bme280_calibration_params = bme280.load_calibration_params(self.bus, self.bme280_address)

        #cold side sensor
        self.ds18b20_sensor = DS18B20()

        #rpm sensor
        self.SENSOR_PIN = 17
        self.MARKS_PER_REV = 1
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.pulse_count = 0
        self.last_time = time.time()

        def pulse_callback(channel):
            self.pulse_count += 1

        GPIO.add_event_detect(self.SENSOR_PIN, GPIO.FALLING, callback=pulse_callback, bouncetime=5)

        #hot side
        self.cs = 19   # Chip Select
        self.sck = 23  # Serial Clock
        self.so = 21   # Serial Output
        max6675.set_pin(self.cs, self.sck, self.so, 1)  # use Celsius output


        # ---- ----- #


        # System state variables
        self.time_elapsed = 0
        self.rpm = 0

        print(f"Connected to InfluxDB at {INFLUXDB_URL}")
        print(f"Writing to bucket: {INFLUXDB_BUCKET}")
        print("Starting TEG Rotor sensor data collection...")
        print("="*60)
    
    def write_data(self):
        timestamp = datetime.utcnow()

        points = [
            Point("rotor_rpm").tag("sensor", "encoder").field("rpm", float(self.rpm)).time(timestamp),
            
            Point("temperature").tag("location", "teg_hot").field("celsius", float(self.teg_hot_temp)).time(timestamp),
            Point("temperature").tag("location", "teg_cold").field("celsius", float(self.teg_cold_temp)).time(timestamp),
            Point("temperature").tag("location", "teg_delta").field("celsius", float(self.teg_hot_temp - self.teg_cold_temp)).time(timestamp),
            Point("temperature").tag("location", "ambient").field("celsius", float(self.ambient_temp)).time(timestamp),
            Point("temperature").tag("location", "rotor_surface").field("celsius", float(self.rotor_surface_temp)).time(timestamp),
            Point("temperature").tag("location", "max6675_hot").field("celsius", float(self.max6675_temp_c)).time(timestamp),
            Point("temperature").tag("location", "ds18b20_cold").field("celsius", float(self.ds18b20_temp_c)).time(timestamp),

            Point("voltage").tag("source", "teg_output").field("volts", float(self.teg_voltage)).time(timestamp),

            Point("fan").field("active", int(self.fan_active)).field("power_watts", float(self.fan_power)).time(timestamp),

            Point("current_sensor").field("bus_voltage", float(self.bus_voltage)).field("bus_current", float(self.bus_current)).
                field("power_mw", float(self.power)).field("shunt_voltage_mv", float(self.shunt_voltage)).time(timestamp),

            Point("air_sensor").field("temperature_c", float(self.air_temp_c)).field("temperature_f", float(self.air_temp_f)).
                field("pressure_hpa", float(self.air_pressure)).field("humidity_percent", float(self.air_humidity)).time(timestamp)
        ]

        try:
            self.write_api.write(bucket=INFLUXDB_BUCKET, record=points)
        except Exception as e:
            print(f"❌ Error writing to InfluxDB: {e}")

    def print_status(self):
        delta_t = self.teg_hot_temp - self.teg_cold_temp
        print(f"\n{'='*70}")
        print(f"⏱️  Time: {datetime.now().strftime('%H:%M:%S')} | Elapsed: {self.time_elapsed}s")
        print(f"🔄 RPM: {self.rpm:7.1f}")
        print(f"🔥 TEG Hot:  {self.teg_hot_temp:5.1f}°C | TEG Cold: {self.teg_cold_temp:5.1f}°C | ΔT: {delta_t:5.1f}°C")
        print(f"🌡️  Ambient: {self.ambient_temp:5.1f}°C | Rotor Surface: {self.rotor_surface_temp:5.1f}°C")
        print(f"⚡ Voltage: {self.teg_voltage:5.2f}V | Fan Power: {self.fan_power:5.2f}W")
        print(f"⚡ Current Sensor: Bus Voltage={self.bus_voltage:.2f}V, Current={self.bus_current:.2f}mA, Power={self.power:.2f}mW, Shunt={self.shunt_voltage:.2f}mV")
        print(f"🌬️  Air Sensor: Temp={self.air_temp_c:.2f}°C ({self.air_temp_f:.2f}°F), Pressure={self.air_pressure:.2f}hPa, Humidity={self.air_humidity:.2f}%")
        print(f"🌡️  Cold Side Temp (DS18B20): {self.ds18b20_temp_c:.2f}°C")
        print(f"🔥 Hot Side Temp (MAX6675): {self.max6675_temp_c:.2f}°C")
        print(f"{'='*70}")
    

    def collect_sensor_data(self):
        self.time_elapsed += 1
        
        # Collect IR sensor data
        self.ambient_temp = self.ir_sensor.get_amb_temp()
        self.teg_hot_temp = self.ir_sensor.get_obj_temp()

        # Collect Current sensor data
        try:
            self.bus_voltage = self.current_sensor.voltage()
            self.bus_current = self.current_sensor.current()
            self.power = self.current_sensor.power()
            self.shunt_voltage = self.current_sensor.shunt_voltage()
        except DeviceRangeError as e:
            print(f"Current sensor error: {e}")
            self.bus_voltage = None
            self.bus_current = None
            self.power = None
            self.shunt_voltage = None
        
        # collect air sensor data
        try:
            data = bme280.sample(self.bus, self.bme280_address, self.bme280_calibration_params)
            self.air_temp_c = data.temperature
            self.air_temp_f = celsius_to_fahrenheit(data.temperature)
            self.air_pressure = data.pressure
            self.air_humidity = data.humidity
        except Exception as e:
            print(f"Error reading air sensor: {e}")
            self.air_temp_c = None
            self.air_temp_f = None
            self.air_pressure = None
            self.air_humidity = None

        #collect cold side data
        try:
            self.ds18b20_temp_c = self.ds18b20_sensor.get_temperature()
        except Exception as e:
            print(f"Error reading DS18B20 sensor: {e}")
            self.ds18b20_temp_c = None

        #collect rpm data
        start_time = time.time()
        start_count = self.pulse_count
        time.sleep(1)
        end_count = self.pulse_count

        pulses = end_count - start_count
        if pulses > 0:
            elapsed = time.time() - start_time
            self.rpm = (pulses / self.MARKS_PER_REV) / elapsed * 60.0
        else:
            self.rpm = 0.0

        #collect hot side data
        try:
            self.max6675_temp_c = max6675.read_temp(self.cs)
            # note: if sensor error occurs it may return a negative number like -22
            if isinstance(self.max6675_temp_c, (int, float)) and self.max6675_temp_c > 0:
                self.max6675_temp_c = round(self.max6675_temp_c, 2)
            else:
                print(f"MAX6675 sensor read error: {self.max6675_temp_c}")
        except Exception as e:
            print(f"Error reading MAX6675: {e}")
            self.max6675_temp_c = None





        



    def run(self, interval=1.0):
        """Run the simulation"""
        iteration = 0
        try:
            while True:
                # self.simulate_physics()
                self.write_data()
                
                # Print status every 5 iterations
                if iteration % 5 == 0:
                    self.print_status()
                
                iteration += 1
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Simulation stopped by user")
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
        finally:
            self.client.close()
            GPIO.cleanup()
            print("👋 Connection closed")

if __name__ == "__main__":
    simulator = TEGRotorSimulator()
    simulator.run(interval=1.0)  # Update every second