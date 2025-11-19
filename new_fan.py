import pigpio

pi = pigpio.pi()

if not pi.connected:
    print("Failed to connect to pi, did you run `sudo pigpiod`?")
    exit()

FAN_GPIO = 18
PWM_RANGE = pi.get_PWM_range(FAN_GPIO)

pi.set_PWM_range(FAN_GPIO, PWM_RANGE)
try:
    while True:
        power = float(input("Set the power in %: ")) * PWM_RANGE / 100
        pi.set_PWM_dutycycle(FAN_GPIO, power)
finally:
    pi.set_PWM_dutycycle(FAN_GPIO, 0)