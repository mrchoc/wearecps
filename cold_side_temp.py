from ds18b20 import DS18B20

sensor = DS18B20()

while True:
    try:
        temperature_in_celsius = sensor.get_temperature()
        # temperature_in_fahrenheit = sensor.get_temperature(DS18B20.DEGREES_F)
        # temperature_in_all_units = sensor.get_temperatures([DS18B20.DEGREES_C, DS18B20.DEGREES_F, DS18B20.KELVIN])

        print(temperature_in_celsius)
    except KeyboardInterrupt:
        print("Program stopped")
        break

