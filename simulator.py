from Adafruit_IO import MQTTClient
import random
import time
from datetime import datetime
import xml.etree.ElementTree as ET
import os

ADAFRUIT_IO_USERNAME = "Elif19"
ADAFRUIT_IO_KEY = "aio_cfPa32MhI58OmHsfScUDmBUKYJof"
FEED_KEYS = [
    "1-park-alaninin-durumu", "2-park-alaninin-durumu",
    "3-park-alaninin-durumu", "4-park-alaninin-durumu",
    "5-park-alaninin-durumu", "6-park-alaninin-durumu",
    "7-park-alaninin-durumu", "8-park-alaninin-durumu"
]

PARK_KATLARI = {
    "1-park-alaninin-durumu": 1,
    "2-park-alaninin-durumu": 1,
    "3-park-alaninin-durumu": 1,
    "4-park-alaninin-durumu": 1,
    "5-park-alaninin-durumu": 2,
    "6-park-alaninin-durumu": 2,
    "7-park-alaninin-durumu": 2,
    "8-park-alaninin-durumu": 2,
}

def connected(client):
    print("Bağlantı başarılı!")

client = MQTTClient(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
client.on_connect = connected
client.connect()
client.loop_background()

# XML log fonksiyonu
def log_message_xml(device, message, is_valid):
    log_file_path = "simulator_log.xml"

    if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > 0:
        try:
            tree = ET.parse(log_file_path)
            root = tree.getroot()
        except ET.ParseError:
            print("Bozuk XML dosyası. Yeniden başlatılıyor.")
            root = ET.Element("logs")
            tree = ET.ElementTree(root)
    else:
        root = ET.Element("logs")
        tree = ET.ElementTree(root)

    log_entry = ET.SubElement(root, "log")

    timestamp = ET.SubElement(log_entry, "timestamp")
    timestamp.text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    device_element = ET.SubElement(log_entry, "device")
    device_element.text = device

    status = ET.SubElement(log_entry, "status")
    status.text = "Geçerli" if is_valid else "Geçersiz"

    message_element = ET.SubElement(log_entry, "message")
    message_element.text = message

    tree.write(log_file_path, encoding="utf-8", xml_declaration=True)

# DFA: her katta boş yer var mı kontrol et
def dfa_validate_floors(status_list):
    floor1 = status_list[:4]
    floor2 = status_list[4:]

    boş1 = floor1.count("BOŞ")
    boş2 = floor2.count("BOŞ")

    if boş1 > 0:
        return True, f"1. katta {boş1} boş park yeri var."
    elif boş2 > 0:
        return True, f"2. katta {boş2} boş park yeri var."
    else:
        return False, "Tüm park alanları dolu."

# Simülasyon döngüsü
while True:
    status_list = []

    for i in range(8):  # 8 park yeri
        if random.random() < 0.15:
            status = "HATALI VERİ"
        else:
            status = random.choice(["DOLU", "BOŞ"])
        status_list.append(status)

    # Yayınla ve logla
    for i in range(8):
        device_id = f"DEV:{i+1:02d}"
        status = status_list[i]
        kat = PARK_KATLARI[FEED_KEYS[i]]
        mesaj = f"Kat {kat} - Park Yeri {i+1}: {status}"
        client.publish(FEED_KEYS[i], mesaj)
        if status == "HATALI VERİ":
            print(f"HATALI: {device_id} - {mesaj}")
            log_message_xml(device_id, status, False)
        else:
            print(f"Durum: {device_id} - {mesaj}")
            log_message_xml(device_id, status, True)

    # DFA analizi
    if "HATALI VERİ" not in status_list:
        is_valid, message = dfa_validate_floors(status_list)
        print("TÜM DURUMLAR:", status_list)
        print("SİSTEM MESAJI:", message)
        log_message_xml("SİSTEM", message, is_valid)
    else:
        print("Geçersiz veriler tespit edildi, DFA çalıştırılmadı.")

    time.sleep(5)
