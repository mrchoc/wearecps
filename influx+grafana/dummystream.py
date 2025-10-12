# dummystream.py - TEG Rotor IoT System Data Simulator
import time
import random
import math
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os

# InfluxDB Configuration
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', 'your-token-here')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'myorg')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'teg_rotor')

# Simulation parameters
RPM_BASELINE = 1200  # RPM threshold for fan activation
RPM_OPTIMAL = 1500   # Target RPM when fan is active

class TEGRotorSimulator:
    def __init__(self):
        self.client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        
        # System state with realistic starting values
        self.rpm = random.uniform(1350, 1450)
        self.fan_active = False
        self.time_elapsed = 0
        
        # Temperature state (Celsius) - initial values
        self.teg_hot_temp = random.uniform(83, 87)
        self.teg_cold_temp = random.uniform(33, 37)
        self.ambient_temp = random.uniform(26, 30)
        self.rotor_surface_temp = random.uniform(72, 78)
        
        # Voltage state (Volts)
        self.teg_voltage = 0.0
        self.fan_power = 0.0
        
        # Trend variables for smooth changes
        self.rpm_trend = 0
        self.ambient_trend = random.uniform(-0.05, 0.05)
        self.load_variation = random.uniform(0.8, 1.2)  # Simulates varying mechanical load
        
        print(f"Connected to InfluxDB at {INFLUXDB_URL}")
        print(f"Writing to bucket: {INFLUXDB_BUCKET}")
        print("Starting TEG Rotor simulation with dynamic data generation...")
        print("="*60)
    
    def simulate_physics(self):
        """Simulate realistic physics with continuous variation"""
        
        self.time_elapsed += 1
        
        # === RPM DYNAMICS ===
        # Natural decay with varying friction (simulates bearing wear, dust, etc.)
        friction_factor = 1.0 + 0.3 * math.sin(self.time_elapsed * 0.01)  # Periodic variation
        rpm_decay = random.uniform(0.8, 1.5) * friction_factor
        
        # Add mechanical load variations (simulates real-world usage)
        self.load_variation += random.uniform(-0.05, 0.05)
        self.load_variation = max(0.7, min(1.3, self.load_variation))
        
        # Apply decay and load
        self.rpm -= rpm_decay * self.load_variation
        
        # Add noise and micro-vibrations
        self.rpm += random.uniform(-8, 8)
        
        # Gradual RPM trends (simulates slow system changes)
        self.rpm_trend += random.uniform(-0.3, 0.3)
        self.rpm_trend = max(-5, min(5, self.rpm_trend))
        self.rpm += self.rpm_trend
        
        # === FAN CONTROL LOGIC ===
        if self.rpm < RPM_BASELINE and not self.fan_active:
            self.fan_active = True
            print(f"⚡ [T+{self.time_elapsed}s] Fan activated! RPM: {self.rpm:.1f}")
        
        if self.fan_active:
            # Fan boost varies based on fan efficiency (degrades over time simulation)
            fan_efficiency = 1.0 - 0.1 * math.sin(self.time_elapsed * 0.02)
            rpm_boost = random.uniform(10, 15) * fan_efficiency
            self.rpm += rpm_boost
            
            # Fan power varies with load
            self.fan_power = random.uniform(2.5, 3.8) * (1 + 0.2 * math.sin(self.time_elapsed * 0.05))
            
            # Deactivate fan with hysteresis
            if self.rpm > RPM_OPTIMAL + 50:  # Add buffer to prevent oscillation
                self.fan_active = False
                self.fan_power = 0.0
                print(f"✓ [T+{self.time_elapsed}s] Fan deactivated. RPM: {self.rpm:.1f}")
        else:
            self.fan_power = 0.0
        
        # Constrain RPM to realistic range
        self.rpm = max(750, min(1850, self.rpm))
        
        # === TEMPERATURE DYNAMICS ===
        # Hot side temperature - affected by RPM and time-varying heat source
        heat_source_variation = 1.0 + 0.15 * math.sin(self.time_elapsed * 0.03)
        target_hot = 78 + (self.rpm / 80) * heat_source_variation
        self.teg_hot_temp += (target_hot - self.teg_hot_temp) * 0.15  # Thermal inertia
        self.teg_hot_temp += random.uniform(-1.5, 1.5)
        
        # Cold side temperature - affected by ambient and cooling efficiency
        cooling_efficiency = 0.9 + 0.1 * math.sin(self.time_elapsed * 0.02)
        target_cold = 28 + (self.ambient_temp * 0.8) / cooling_efficiency
        self.teg_cold_temp += (target_cold - self.teg_cold_temp) * 0.12
        self.teg_cold_temp += random.uniform(-1.2, 1.2)
        
        # Ambient temperature - slow drift with daily cycles
        daily_cycle = 2.0 * math.sin(self.time_elapsed * 0.001)  # Very slow cycle
        self.ambient_trend += random.uniform(-0.02, 0.02)
        self.ambient_trend = max(-0.1, min(0.1, self.ambient_trend))
        self.ambient_temp += self.ambient_trend + daily_cycle * 0.01
        self.ambient_temp += random.uniform(-0.3, 0.3)
        self.ambient_temp = max(22, min(34, self.ambient_temp))
        
        # Rotor surface temperature - correlates with RPM and friction
        friction_heat = friction_factor * 5
        target_rotor = 55 + (self.rpm / 45) + friction_heat
        self.rotor_surface_temp += (target_rotor - self.rotor_surface_temp) * 0.18
        self.rotor_surface_temp += random.uniform(-2.5, 2.5)
        
        # === VOLTAGE CALCULATION ===
        # TEG voltage depends on temperature differential (Seebeck effect)
        delta_t = self.teg_hot_temp - self.teg_cold_temp
        
        # Seebeck coefficient varies slightly with temperature and age
        seebeck_coeff = 0.078 + 0.005 * math.sin(self.time_elapsed * 0.008)
        
        # Calculate voltage with efficiency losses
        teg_efficiency = 0.95 + 0.05 * math.sin(self.time_elapsed * 0.015)
        self.teg_voltage = (delta_t * seebeck_coeff * teg_efficiency)
        self.teg_voltage += random.uniform(-0.15, 0.15)
        self.teg_voltage = max(0, self.teg_voltage)
    
    def write_data(self):
        """Write sensor data to InfluxDB"""
        
        timestamp = datetime.utcnow()
        
        # RPM measurement
        rpm_point = Point("rotor_rpm") \
            .tag("sensor", "encoder") \
            .field("rpm", float(self.rpm)) \
            .time(timestamp)
        
        # Temperature measurements
        temp_hot_point = Point("temperature") \
            .tag("location", "teg_hot") \
            .field("celsius", float(self.teg_hot_temp)) \
            .time(timestamp)
        
        temp_cold_point = Point("temperature") \
            .tag("location", "teg_cold") \
            .field("celsius", float(self.teg_cold_temp)) \
            .time(timestamp)
        
        delta_t = self.teg_hot_temp - self.teg_cold_temp
        temp_delta_point = Point("temperature") \
            .tag("location", "teg_delta") \
            .field("celsius", float(delta_t)) \
            .time(timestamp)
        
        ambient_point = Point("temperature") \
            .tag("location", "ambient") \
            .field("celsius", float(self.ambient_temp)) \
            .time(timestamp)
        
        rotor_temp_point = Point("temperature") \
            .tag("location", "rotor_surface") \
            .field("celsius", float(self.rotor_surface_temp)) \
            .time(timestamp)
        
        # Voltage measurements
        teg_voltage_point = Point("voltage") \
            .tag("source", "teg_output") \
            .field("volts", float(self.teg_voltage)) \
            .time(timestamp)
        
        # Fan status and power
        fan_status_point = Point("fan") \
            .field("active", int(self.fan_active)) \
            .field("power_watts", float(self.fan_power)) \
            .time(timestamp)
        
        # Write all points
        points = [
            rpm_point, temp_hot_point, temp_cold_point, temp_delta_point,
            ambient_point, rotor_temp_point, teg_voltage_point, fan_status_point
        ]
        
        try:
            self.write_api.write(bucket=INFLUXDB_BUCKET, record=points)
        except Exception as e:
            print(f"❌ Error writing to InfluxDB: {e}")
    
    def print_status(self):
        """Print current system status"""
        delta_t = self.teg_hot_temp - self.teg_cold_temp
        print(f"\n{'='*70}")
        print(f"⏱️  Time: {datetime.now().strftime('%H:%M:%S')} | Elapsed: {self.time_elapsed}s")
        print(f"🔄 RPM: {self.rpm:7.1f} {'🌀[FAN ON]' if self.fan_active else '         '} | Load: {self.load_variation:.2f}x")
        print(f"🔥 TEG Hot:  {self.teg_hot_temp:5.1f}°C | TEG Cold: {self.teg_cold_temp:5.1f}°C | ΔT: {delta_t:5.1f}°C")
        print(f"🌡️  Ambient: {self.ambient_temp:5.1f}°C | Rotor:    {self.rotor_surface_temp:5.1f}°C")
        print(f"⚡ TEG Out:  {self.teg_voltage:5.2f}V  | Fan:      {self.fan_power:5.2f}W")
        print(f"{'='*70}")
    
    def run(self, interval=1.0):
        """Run the simulation"""
        iteration = 0
        try:
            while True:
                self.simulate_physics()
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
            print("👋 Connection closed")

if __name__ == "__main__":
    simulator = TEGRotorSimulator()
    simulator.run(interval=1.0)  # Update every second