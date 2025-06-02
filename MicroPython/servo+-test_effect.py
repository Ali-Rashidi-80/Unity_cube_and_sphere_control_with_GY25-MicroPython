# Ali Rashidi
# t.me/WriteYourway

from machine import Pin, PWM
from time import sleep

# تابع برای تبدیل زاویه به مقدار PWM مناسب برای سروو
def angle_to_duty(angle):
    min_duty = 1400  # مقدار مناسب برای 0 درجه (ممکن است برای برخی سرووها 500 باشد)
    max_duty = 8000  # مقدار مناسب برای 180 درجه (ممکن است برای برخی سرووها 2500 باشد)
    return int((angle / 180) * (max_duty - min_duty) + min_duty)  # تنظیم دقیق‌تر

# تعریف پایه‌های سروو
servo_pins = [PWM(Pin(28)), PWM(Pin(27)), PWM(Pin(26))]

# تنظیم فرکانس PWM
for servo in servo_pins:
    servo.freq(50)

while True:
    # حرکت آرام سرووها از 0 تا 180 درجه
    for angle in range(0, 181, 2):
        duty = angle_to_duty(angle)
        for servo in servo_pins:
            servo.duty_u16(duty)
        sleep(0.02)  # مکث کوتاه برای حرکت نرم
    sleep(0.1)
    
    # حرکت آرام سرووها از 180 به 0 درجه
    for angle in range(180, -1, -2):
        duty = angle_to_duty(angle)
        for servo in servo_pins:
            servo.duty_u16(duty)
        sleep(0.02)  # مکث کوتاه برای حرکت نرم
