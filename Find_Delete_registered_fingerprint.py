import adafruit_fingerprint
import serial

# Setup Serial Communication
uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.AdafruitFingerprint(uart)

def delete_all_fingerprints():
    
    print("\n🗑️ Deleting all fingerprints...")

    try:
        result = finger.empty()

        if result == 0:
            print("✅ All fingerprints have been successfully deleted.")
        else:
            print(f"⚠️ Error deleting fingerprints. Error Code: {result}")

    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")

def check_fingerprint_storage():
    
    print("\n📋 Checking stored fingerprints...")

    try:
        total_templates = finger.template_num()[1]

        print(f"✅ Total Registered Fingerprints: {total_templates}")

        if total_templates == 0:
            print("🧹 All fingerprints have been deleted. Storage is empty.")
        else:
            print("⚠️ Some fingerprints are still stored in the sensor.")

    except Exception as e:
        print(f"⚠️ Error: {e}")

check_fingerprint_storage()
delete_all_fingerprints()
check_fingerprint_storage()