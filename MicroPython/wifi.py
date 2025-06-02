# Ali Rashidi
# t.me/WriteYourway

import network
import time

# اطلاعات شبکه WiFi
SSID = "Wokwi-GUEST"  # نام شبکه
PASSWORD = ""  # رمز عبور

# مقداردهی اولیه WLAN
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# تابع اتصال به WiFi
def connect_wifi():
    if wlan.isconnected():
        print("✅ Already connected. IP Address:", wlan.ifconfig()[0])
        wifi_status()
        return True

    print("\n🔄 Connecting to WiFi...")
    wlan.connect(SSID, PASSWORD)

    timeout = 10  # حداکثر زمان تلاش برای اتصال (ثانیه)
    start_time = time.time()

    while not wlan.isconnected():
        if time.time() - start_time > timeout:
            print("\n❌ Connection timed out!")
            return False
        print(".", end="")
        time.sleep(1)

    print("\n✅ Connected! IP Address:", wlan.ifconfig()[0])
    return True

# بررسی وضعیت WiFi
def wifi_status():
    if wlan.isconnected():
        ip, subnet, gateway, dns = wlan.ifconfig()
        print("\n📡 WiFi Info:")
        print(f"  - IP Address: {ip}")
        print(f"  - Subnet Mask: {subnet}")
        print(f"  - Gateway: {gateway}")
        print(f"  - DNS Server: {dns}")
    else:
        print("\n❌ Not connected to WiFi")

# تابع بررسی و بازیابی اتصال WiFi
def ensure_wifi_connection():
    if not wlan.isconnected():
        print("\n⚠ WiFi lost! Reconnecting...")
        return connect_wifi()
    return True

# اجرای اتصال اولیه
#if connect_wifi():
#    wifi_status()
#else:
#    print("\n⚠ Running in offline mode.")


#while True:
#    ensure_wifi_connection()
#    time.sleep(10)  # بررسی هر 10 ثانیه
