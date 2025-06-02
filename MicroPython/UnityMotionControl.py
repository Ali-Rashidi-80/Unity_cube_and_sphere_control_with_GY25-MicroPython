"""
# Ali Rashidi
# t.me/WriteYourway
# UnityMotionControl

1. سرور ارسال داده‌های MPU6050 (پورت: 8800)
2. سرور کنترل سروو (پورت: 8765)
"""

import uasyncio as asyncio             # وارد کردن ماژول uasyncio برای برنامه‌نویسی به‌صورت غیرهمزمان (async)
import ujson                           # وارد کردن ماژول ujson جهت رمزگشایی و کدگذاری داده‌های JSON
import ubinascii                       # وارد کردن ماژول ubinascii جهت تبدیل داده‌های باینری
import hashlib                         # وارد کردن ماژول hashlib برای محاسبات هش (SHA1)
import math                            # وارد کردن ماژول math جهت انجام محاسبات ریاضی
import utime                           # وارد کردن ماژول utime برای انجام عملیات زمانی (مثلاً تاخیر)
from machine import Pin, PWM           # وارد کردن کلاس‌های Pin و PWM از ماژول machine جهت کنترل سخت‌افزار
from time import sleep_ms              # وارد کردن تابع sleep_ms از ماژول time برای ایجاد تاخیرهای میلی‌ثانیه‌ای

import wifi                            # وارد کردن ماژول wifi که شامل توابع connect_wifi(), ensure_wifi_connection() و متغیر wlan است
from mpu6050 import MPU6050            # وارد کردن کلاس MPU6050 جهت خواندن داده از حسگر MPU6050

# ====================== تنظیمات عمومی ======================

# تابع غیرهمزمان برای اطمینان از اتصال به WiFi
async def ensure_wifi():
    # در حالی که اتصال WiFi برقرار نیست، تلاش برای اتصال انجام می‌شود
    while not wifi.wlan.isconnected():
        wifi.connect_wifi()            # فراخوانی تابع اتصال به WiFi
        wifi.wifi_status()
        await asyncio.sleep(2)         # توقف غیرهمزمان به مدت 2 ثانیه قبل از تلاش مجدد
    wifi.ensure_wifi_connection()      # بررسی نهایی اتصال و اطمینان از پایداری اتصال
    # چاپ آدرس IP پس از برقراری اتصال موفق
    print("WiFi متصل است. IP Address:", wifi.wlan.ifconfig()[0])
    print(f"\n")

# ایجاد یک نمونه از کلاس MPU6050 جهت خواندن داده‌های حسگر
mpu = MPU6050()                        # نمونه‌سازی از MPU6050

# ====================== توابع و کلاس‌های WebSocket ======================

# تابع ایجاد کلید پذیرش (Accept Key) برای handshake پروتکل WebSocket
def create_accept_key(key):
    GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'   # GUID استاندارد مورد نیاز برای محاسبه کلید پذیرش
    sha1 = hashlib.sha1((key + GUID).encode()).digest()  # محاسبه هش SHA1 کلید دریافتی به همراه GUID
    return ubinascii.b2a_base64(sha1).strip().decode()      # تبدیل هش به Base64 و برگرداندن رشته نتیجه

# تابع غیرهمزمان برای انجام handshake پروتکل WebSocket
async def websocket_handshake(reader, writer):
    try:
        req = await reader.read(1024)        # خواندن درخواست handshake از کلاینت (تا 1024 بایت)
        req_str = req.decode()                 # تبدیل داده‌های باینری به رشته
    except Exception as e:
        print("خطا در خواندن درخواست:", e)    # چاپ خطا در صورت بروز استثناء
        return False                         # بازگرداندن False در صورت خطا
    if 'Sec-WebSocket-Key:' not in req_str:    # بررسی وجود هدر Sec-WebSocket-Key در درخواست
        return False                         # در صورت نبود، handshake ناموفق است
    try:
        # استخراج مقدار کلید از هدر
        key = req_str.split('Sec-WebSocket-Key: ')[1].split('\r\n')[0].strip()
    except Exception as e:
        print("خطا در پردازش کلید handshake:", e)  # چاپ خطا در صورت بروز استثناء
        return False                         # بازگرداندن False در صورت خطا
    accept_key = create_accept_key(key)        # محاسبه کلید پذیرش با استفاده از تابع ایجاد کلید
    # ایجاد پاسخ handshake بر اساس پروتکل WebSocket
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Accept: {}\r\n\r\n".format(accept_key)
    )
    writer.write(response.encode())          # ارسال پاسخ handshake به کلاینت
    await writer.drain()                       # اطمینان از ارسال کامل داده‌ها به کلاینت
    return True                                # بازگرداندن True به عنوان موفقیت‌آمیز بودن handshake

# تابع ساخت فریم ساده WebSocket جهت ارسال پیام متنی کوتاه
def build_frame(data_bytes):
    """ساخت فریم ساده WebSocket (فقط برای پیام‌های متنی کوتاه)"""
    frame = bytearray()                        # ایجاد یک آرایه بایت خالی جهت ساخت فریم
    frame.append(0x81)                         # افزودن بایت اول فریم: FIN=1 (پایان پیام) و opcode=1 (متن)
    payload_length = len(data_bytes)           # محاسبه طول payload
    if payload_length < 126:                   # اگر طول payload کمتر از 126 بایت باشد
        frame.append(payload_length)           # افزودن طول payload به فریم
    elif payload_length < (1 << 16):           # اگر طول payload بین 126 تا 65535 باشد
        frame.append(126)                      # افزودن نشانگر طول 126 به فریم
        frame.extend(payload_length.to_bytes(2, 'big'))  # افزودن طول payload به صورت 2 بایتی
    else:                                      # اگر طول payload بزرگتر از 65535 باشد
        frame.append(127)                      # افزودن نشانگر طول 127 به فریم
        frame.extend(payload_length.to_bytes(8, 'big'))  # افزودن طول payload به صورت 8 بایتی
    frame.extend(data_bytes)                   # افزودن داده‌های payload به فریم
    return frame                               # برگرداندن فریم ساخته‌شده

# تابع پردازش فریم دریافتی WebSocket جهت استخراج opcode و payload
def parse_frame(data):
    """
    پردازش فریم ساده WebSocket.
    این تابع تنها پیام‌های متنی با payload کوتاه (بدون تکه‌بندی) را پردازش می‌کند.
    """
    if len(data) < 2:                          # اگر طول داده کمتر از 2 بایت باشد، پردازش غیرممکن است
        return None
    byte1 = data[0]                            # استخراج بایت اول فریم
    byte2 = data[1]                            # استخراج بایت دوم فریم
    opcode = byte1 & 0x0F                      # استخراج opcode از بایت اول (پایین‌ترین 4 بیت)
    masked = byte2 & 0x80                      # بررسی وضعیت masked بودن payload (بیت بالایی بایت دوم)
    payload_len = byte2 & 0x7F                 # استخراج طول payload از بایت دوم (7 بیت پایین)
    idx = 2                                    # اندیس شروع داده‌های اضافی در فریم
    if payload_len == 126:                     # اگر payload به صورت 126 اعلام شده باشد
        payload_len = int.from_bytes(data[idx:idx+2], 'big')  # خواندن طول payload از 2 بایت بعدی
        idx += 2                             # افزایش اندیس به اندازه 2 بایت
    elif payload_len == 127:                   # اگر payload به صورت 127 اعلام شده باشد
        payload_len = int.from_bytes(data[idx:idx+8], 'big')  # خواندن طول payload از 8 بایت بعدی
        idx += 8                             # افزایش اندیس به اندازه 8 بایت
    if masked:                                 # اگر داده‌های payload masked شده باشند
        mask_key = data[idx:idx+4]             # استخراج کلید mask از 4 بایت
        idx += 4                             # افزایش اندیس به اندازه 4 بایت برای داده‌های payload
        payload = bytearray()                  # ایجاد یک آرایه بایت خالی جهت ذخیره payload رمزگشایی‌شده
        for i in range(payload_len):           # حلقه بر روی تمام بایت‌های payload
            payload.append(data[idx+i] ^ mask_key[i % 4])  # انجام عملیات XOR برای رمزگشایی هر بایت
    else:
        payload = data[idx:idx+payload_len]     # اگر masked نباشد، payload به صورت مستقیم استخراج می‌شود
    return opcode, payload                     # برگرداندن opcode و payload استخراج‌شده

# ====================== سرور MPU (ارسال داده‌های حسگر) ======================

# تابع محاسبه زاویه‌ها (pitch, roll, yaw) از داده‌های شتاب‌سنج
def calculate_angles(accel_data):
    Ax, Ay, Az = accel_data["x"], accel_data["y"], accel_data["z"]  # استخراج مقادیر محورهای x, y, z
    pitch = math.atan2(Ay, math.sqrt(Ax**2 + Az**2)) * 180 / math.pi    # محاسبه زاویه pitch به درجه
    roll  = math.atan2(-Ax, math.sqrt(Ay**2 + Az**2)) * 180 / math.pi     # محاسبه زاویه roll به درجه
    yaw   = math.atan2(Ax, Ay) * 180 / math.pi                           # محاسبه زاویه yaw به درجه
    return pitch, roll, yaw                                            # برگرداندن زاویه‌های محاسبه‌شده

# تابع محاسبه شتاب به عنوان g-force از داده‌های شتاب‌سنج
def calculate_gforce(accel_data):
    Ax, Ay, Az = accel_data["x"], accel_data["y"], accel_data["z"]  # استخراج مقادیر محورهای x, y, z
    return math.sqrt(Ax**2 + Ay**2 + Az**2)                            # محاسبه و برگرداندن g-force (مجموع مربعات)

# تابع handler غیرهمزمان برای مدیریت ارتباط WebSocket جهت ارسال داده‌های حسگر MPU
async def mpu_client_handler(reader, writer):
    if not await websocket_handshake(reader, writer):  # انجام handshake با کلاینت
        writer.close()                                   # بستن اتصال در صورت عدم موفقیت handshake
        await writer.wait_closed()                       # انتظار برای بسته شدن کامل اتصال
        return                                           # خروج از تابع
    print("اتصال WebSocket MPU برقرار شد")             # چاپ پیام موفقیت handshake
    try:
        while True:                                      # حلقه بی‌نهایت جهت ارسال داده‌ها
            # خواندن داده از حسگر MPU6050
            accel = mpu.read_accel_data()                # خواندن داده‌های شتاب‌سنج
            pitch, roll, yaw = calculate_angles(accel)   # محاسبه زاویه‌های مربوطه
            gyro = mpu.read_gyro_data()                  # خواندن داده‌های ژیروسکوپ
            # ساخت دیکشنری داده جهت ارسال به کلاینت
            data = {
                "posX": pitch,                         # ارسال زاویه pitch به عنوان posX
                "posY": roll,                          # ارسال زاویه roll به عنوان posY
                "posZ": yaw,                           # ارسال زاویه yaw به عنوان posZ
                "gyroX": gyro["x"],                    # ارسال مقدار محور x ژیروسکوپ
                "gyroY": gyro["y"],                    # ارسال مقدار محور y ژیروسکوپ
                "gyroZ": gyro["z"]                     # ارسال مقدار محور z ژیروسکوپ
            }
            encoded = ujson.dumps(data).encode('utf-8')  # رمزگذاری دیکشنری داده به JSON و تبدیل به بایت
            frame = build_frame(encoded)               # ساخت فریم WebSocket از داده‌های رمزگذاری‌شده
            writer.write(frame)                        # ارسال فریم به کلاینت
            await writer.drain()                       # اطمینان از ارسال کامل داده‌ها
            await asyncio.sleep_ms(100)                 # توقف غیرهمزمان به مدت 100 میلی‌ثانیه قبل از ارسال مجدد
    except Exception as e:
        print("خطای سرور MPU:", e)                      # در صورت بروز خطا، چاپ جزئیات خطا
    finally:
        try:
            writer.close()                             # بستن اتصال writer
            await writer.wait_closed()                 # انتظار برای بسته شدن کامل اتصال
        except Exception as e:
            print("خطا در بستن اتصال MPU:", e)         # در صورت بروز خطا در بسته‌شدن اتصال، چاپ خطا
        print("ارتباط با کلاینت MPU قطع شد.")            # چاپ پیام قطع ارتباط

# تابع غیرهمزمان جهت راه‌اندازی سرور MPU (ارسال داده‌های حسگر) روی پورت 8800
async def start_mpu_server():
    server = await asyncio.start_server(mpu_client_handler, "0.0.0.0", 8800)  # راه‌اندازی سرور جهت دریافت اتصالات
    # چاپ پیام شروع سرور
    print("سرور MPU روی پورت 8800 شروع به کار کرد")
    print("MPU server started on port 8800")  
    print(f"\n")
    # استفاده از حلقه بی‌نهایت جهت جلوگیری از خاتمه یافتن تابع
    while True:
        await asyncio.sleep(1)                           # توقف غیرهمزمان به مدت 1 ثانیه و ادامه حلقه

# ====================== سرور سروو (دریافت دستورات و کنترل سروو) ======================

# تنظیمات PWM و سروو
PWM_FREQ = 50         # فرکانس PWM (Hz)
PWM_MIN = 1400        # حداقل مقدار PWM برای زاویه 0 درجه
PWM_MAX = 8000        # حداکثر مقدار PWM برای زاویه 180 درجه

# تابع نگاشت مقدار از یک بازه به بازه دیگر
def map_value(x, in_min, in_max, out_min, out_max):
    return out_min + (x - in_min) * (out_max - out_min) / (in_max - in_min)  # محاسبه مقدار نگاشتی

# کلاس کنترل سروو جهت تنظیم زوایای سرووها
class ServoController:
    def __init__(self, pins):
        # ایجاد لیستی از اشیاء PWM برای هر پین داده‌شده
        self.servos = [PWM(Pin(pin, Pin.OUT)) for pin in pins]
        for servo in self.servos:         # تنظیم فرکانس PWM برای هر سروو
            servo.freq(PWM_FREQ)
    
    # تابع تنظیم زاویه سروو مشخص‌شده
    def set_angle(self, servo_num, target_angle):
        target_angle = max(0, min(180, target_angle))  # محدود کردن زاویه ورودی بین 0 و 180 درجه
        duty = int(map_value(target_angle, 0, 180, PWM_MIN, PWM_MAX))  # محاسبه مقدار duty cycle متناظر با زاویه
        self.servos[servo_num].duty_u16(duty)          # تنظیم مقدار duty cycle سروو انتخاب‌شده
        print("سروو {} به {}° تنظیم شد.".format(servo_num, target_angle))  # چاپ پیام تنظیم زاویه سروو
        utime.sleep_ms(20)                             # توقف کوتاه جهت تثبیت تغییرات
    
    # تابع آزادسازی سرووها (بستن PWM)
    def release_all(self):
        for servo in self.servos:         # برای هر سروو، عملیات deinit انجام می‌شود
            servo.deinit()

# ایجاد یک نمونه از ServoController برای پین‌های مشخص (در اینجا 28, 27, 26)
servo_ctl = ServoController([28, 27, 26])

# تابع handler غیرهمزمان برای مدیریت ارتباط WebSocket جهت دریافت دستورات سروو
async def servo_client_handler(reader, writer):
    if not await websocket_handshake(reader, writer):  # انجام handshake با کلاینت سروو
        writer.close()                                   # بستن اتصال در صورت عدم موفقیت handshake
        await writer.wait_closed()                       # انتظار برای بسته‌شدن کامل اتصال
        return                                           # خروج از تابع
    print("اتصال WebSocket سروو برقرار شد")            # چاپ پیام موفقیت handshake
    try:
        while True:                                      # حلقه بی‌نهایت جهت دریافت داده‌ها از کلاینت
            data = await reader.read(1024)               # خواندن داده (تا 1024 بایت) از کلاینت
            if not data:                                 # اگر داده‌ای دریافت نشد، حلقه قطع می‌شود
                break
            frame = parse_frame(data)                    # پردازش داده‌های دریافتی به منظور استخراج فریم
            if frame is None:                            # اگر فریم به درستی پردازش نشد، ادامه حلقه
                continue
            opcode, payload = frame                      # استخراج opcode و payload از فریم
            if opcode == 0x08:                           # اگر opcode برابر با 0x08 (درخواست بستن ارتباط) باشد
                break                                  # خروج از حلقه
            if opcode == 0x01:                           # اگر opcode برابر با 0x01 (پیام متنی) باشد
                try:
                    msg = ujson.loads(payload.decode('utf-8'))  # رمزگشایی payload از JSON به دیکشنری
                    print("پیام دریافتی برای سروو:", msg)         # چاپ پیام دریافتی
                    # انتظار می‌رود پیام شامل کلیدهای "posX", "posY" و "posZ" باشد
                    for axis in ['X', 'Y', 'Z']:                   # حلقه بر روی محورهای X, Y, Z
                        key = "pos" + axis                        # ساخت کلید مربوطه (مثلاً "posX")
                        if key in msg:                            # بررسی وجود کلید در پیام دریافتی
                            try:
                                angle = int(msg[key])             # تبدیل مقدار دریافت‌شده به عدد صحیح (زاویه)
                                servo_num = ord(axis) - ord('X')    # محاسبه شماره سروو بر اساس محور (X=0, Y=1, Z=2)
                                servo_ctl.set_angle(servo_num, angle)  # تنظیم زاویه سروو مربوطه
                            except Exception as e:
                                # در صورت بروز خطا در پردازش زاویه، چاپ پیام خطا
                                print("خطا در پردازش زاویه برای {}: {}".format(axis, e))
                except Exception as e:
                    print("خطا در پردازش پیام سروو:", e)        # چاپ خطا در پردازش پیام‌های سروو
    except Exception as e:
        print("خطای سرور سروو:", e)                          # چاپ خطا در ارتباط با کلاینت سروو
    finally:
        try:
            writer.close()                                  # بستن اتصال writer
            await writer.wait_closed()                      # انتظار برای بسته شدن کامل اتصال
        except Exception as e:
            print("خطا در بستن اتصال سروو:", e)             # چاپ خطا در صورت مشکل در بستن اتصال
        print("ارتباط با کلاینت سروو قطع شد.")                # چاپ پیام قطع ارتباط با کلاینت سروو

# تابع غیرهمزمان جهت راه‌اندازی سرور سروو روی پورت 8765
async def start_servo_server():
    server = await asyncio.start_server(servo_client_handler, "0.0.0.0", 8765)  # راه‌اندازی سرور سروو جهت دریافت اتصالات
    # چاپ پیام شروع سرور سروو
    print("سرور سروو روی پورت 8765 شروع به کار کرد") 
    print("Servo server started running on port 8765")  
    print(f"\n")
    # استفاده از حلقه بی‌نهایت جهت جلوگیری از خاتمه یافتن تابع
    while True:
        await asyncio.sleep(1)                          # توقف غیرهمزمان به مدت 1 ثانیه و ادامه حلقه

# ====================== تابع اصلی ======================

# تابع اصلی غیرهمزمان جهت اجرای هر دو سرور به‌صورت همزمان
async def main():
    await ensure_wifi()                                 # اطمینان از برقراری اتصال WiFi قبل از شروع سرورها
    # اجرای همزمان سرور MPU و سرور سروو با استفاده از asyncio.gather
    await asyncio.gather(
        start_mpu_server(),                             # شروع سرور ارسال داده‌های MPU (پورت 8800)
        start_servo_server()                            # شروع سرور کنترل سروو (پورت 8765)
    )

# ====================== اجرای برنامه ======================

def start():
    asyncio.run(main())                                     # اجرای تابع main به صورت غیرهمزمان به کمک asyncio.run
