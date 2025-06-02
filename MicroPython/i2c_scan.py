# Ali Rashidi
# t.me/WriteYourway

from machine import SoftI2C, Pin
import time

# مقداردهی اولیه I2C
try:
    i2c = SoftI2C(scl=Pin(2), sda=Pin(3), freq=400000)
    print("I2C initialized successfully.")
except Exception as e:
    print("Error initializing I2C:", e)
    i2c = None  # در صورت خطا مقدار None می‌گیرد

# اسکن دستگاه‌ها
def scan_i2c():
    if i2c is None:
        print("I2C is not initialized.")
        return

    devices = i2c.scan()
    
    if not devices:
        print("No I2C devices found.")
    else:
        print(f"Found {len(devices)} I2C device(s):")
        for device in devices:
            print(f" - Address: 0x{device:02X}")

# اجرای اسکن هر ۵ ثانیه
while True:
    scan_i2c()
    time.sleep(5)
