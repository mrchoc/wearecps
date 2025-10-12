import time
from smbus2 import SMBus
from mlx90614 import MLX90614

bus = SMBus(1)
sensor = MLX90614(bus, address=0x5A)

while True:
    try:
        print(f'Ambient temperature: {sensor.get_amb_temp()}')
        print(f'Object temperature: {sensor.get_obj_temp()}')

        time.sleep(1)
    except KeyboardInterrupt:
        print('Program stopped')
        break 
    except Exception as e:
        print('An unexpected error occurred:', str(e))
        break
bus.close()
