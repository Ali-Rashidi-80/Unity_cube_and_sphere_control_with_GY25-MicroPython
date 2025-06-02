# Ali Rashidi
# t.me/WriteYourway

from mpu6050 import MPU6050
from machine import Pin
from time import sleep_ms, ticks_ms
import math

mpu = MPU6050()

def calculate_angles(accel_data):
    # محاسبه زاویه Pitch و Roll
    Ax, Ay, Az = accel_data["x"], accel_data["y"], accel_data["z"]
    
    pitch = math.atan2(Ay, math.sqrt(Ax**2 + Az**2)) * 180 / math.pi  # تبدیل به درجه
    roll = math.atan2(-Ax, math.sqrt(Ay**2 + Az**2)) * 180 / math.pi  # تبدیل به درجه
    yaw = math.atan2(Ax, Ay) * 180 / math.pi  # تبدیل به درجه برای Yaw
    
    # محدود کردن مقادیر Pitch و Roll به 0 تا 180 درجه
    #pitch = max(0, min(pitch, 180))
    #roll = max(0, min(roll, 180))
    #yaw = max(0, min(yaw, 180))  # محدود کردن Yaw به 0 تا 90 درجه  

    return pitch, roll, yaw

def calculate_gforce(accel_data):
    # محاسبه G-Force
    Ax, Ay, Az = accel_data["x"], accel_data["y"], accel_data["z"]
    gforce = math.sqrt(Ax**2 + Ay**2 + Az**2)
    return gforce

prev_time = ticks_ms()
pitch = 0
roll = 0

while True:
    # داده‌های شتاب‌سنج
    accel = mpu.read_accel_data() #[m/s²]
    pitch, roll, yaw = calculate_angles(accel) 
    temp = mpu.read_temperature()  # [°C]
    
    # داده‌های ژیروسکوپ
    gyro = mpu.read_gyro_data() #[deg/s]
    gyro_x = gyro["x"]
    gyro_y = gyro["y"]
    gyro_z = gyro["z"]
    
    # زمان برای محاسبه تغییرات زاویه‌ای
    curr_time = ticks_ms()
    dt = (curr_time - prev_time) / 1000  # ثانیه
    prev_time = curr_time
    
    # محاسبه تغییرات زاویه‌ای (ژایرو)
    angle_x = gyro_x * dt
    angle_y = gyro_y * dt
    angle_z = gyro_z * dt
    
    # محاسبه G-Force
    gforce = calculate_gforce(accel)
    
    # چاپ نتایج
    #print("\n")
    #print(f"="*50)
    print(f"Accelerometer -->  X: {pitch:.2f} , Y: {roll:.2f} , Z: {yaw:.2f} , G-Force: {gforce:.2f} g")
    #print(f"."*50)
    print(f"."*50)
    print(f"Gyroscope -->  X: {angle_x:.2f} , Y: {angle_y:.2f} , Z: {angle_z:.2f} deg")
    print(f"temp: {temp} °C\n")
    #print(f"="*50)

    sleep_ms(300)
