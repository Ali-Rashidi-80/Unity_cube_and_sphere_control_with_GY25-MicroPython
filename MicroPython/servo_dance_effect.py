# Ali Rashidi
# t.me/WriteYourway

from machine import Pin, PWM
import time
import random
import math

# تعریف پین‌های سروو
servo1_pin = 28  
servo2_pin = 27  
servo3_pin = 26  

# تنظیم PWM برای هر سروو
servo1 = PWM(Pin(servo1_pin))
servo1.freq(50)

servo2 = PWM(Pin(servo2_pin))
servo2.freq(50)

servo3 = PWM(Pin(servo3_pin))
servo3.freq(50)

# تابع برای تنظیم زاویه سروو
def set_servo_angle(servo, angle):
    min_duty = 1638   # مقدار کمینه (0 درجه)
    max_duty = 8192   # مقدار بیشینه (180 درجه)
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    servo.duty_u16(duty)

# تابع برای اجرای الگوی رقص ترکیبی
def dance_effect():
    # مرحله ۱: حرکات تصادفی پرانرژی  
    for _ in range(8):  
        set_servo_angle(servo1, random.randint(30, 150))
        set_servo_angle(servo2, random.randint(30, 150))
        set_servo_angle(servo3, random.randint(30, 150))
        time.sleep(random.uniform(0.1, 0.3))  

    # مرحله ۲: حرکت موجی سینوسی  
    for i in range(0, 360, 10):  
        angle1 = 90 + 50 * math.sin(math.radians(i))
        angle2 = 90 + 50 * math.sin(math.radians(i + 120))
        angle3 = 90 + 50 * math.sin(math.radians(i + 240))
        set_servo_angle(servo1, angle1)
        set_servo_angle(servo2, angle2)
        set_servo_angle(servo3, angle3)
        time.sleep(0.05)  

    # مرحله ۳: حرکات متقاطع و ترکیبی  
    for angle in range(0, 180, 15):
        set_servo_angle(servo1, angle)
        set_servo_angle(servo2, 180 - angle)
        set_servo_angle(servo3, angle // 2)
        time.sleep(0.08)

    for angle in range(180, 0, -15):
        set_servo_angle(servo1, angle)
        set_servo_angle(servo2, 180 - angle)
        set_servo_angle(servo3, angle // 2)
        time.sleep(0.08)

# حلقه اجرای مداوم
while True:
    dance_effect()
