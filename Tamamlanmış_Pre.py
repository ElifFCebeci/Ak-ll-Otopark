import random
import time
import os
import re
from datetime import datetime
import xml.etree.ElementTree as ET
from Adafruit_IO import MQTTClient

# MQTT Ayarları
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

# MQTT bağlandığında

def connected(client):
    print("Bağlantı başarılı!")

client = MQTTClient(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
client.on_connect = connected
client.connect()
client.loop_background()

# XML protokol kurallarını yükle

def load_protocol(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    header_pattern = root.find('./message/header').attrib['pattern']
    body_fields = root.findall('./message/body/field')
    body_patterns = [f.attrib['pattern'] for f in body_fields]
    footer_pattern = root.find('./message/footer').attrib['pattern']

    return header_pattern, body_patterns, footer_pattern

# XML mesajı doğrula

def validate_message(message, header_pattern, body_patterns, footer_pattern):
    pos = 0

    header_match = re.match(header_pattern, message[pos:])
    if not header_match:
        return False, "Header hatalı"
    pos += header_match.end()

    for pattern in body_patterns:
        match = re.match(pattern, message[pos:])
        if not match:
            return False, f"Body hatalı: {pattern}"
        pos += match.end()

    footer_match = re.match(footer_pattern, message[pos:])
    if not footer_match:
        return False, "Footer hatalı"
    pos += footer_match.end()

    if pos != len(message):
        return False, "Fazla veri var"

    return True, "Mesaj geçerli"

# XML log

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

# Protokol yükle
header_pattern, body_patterns, footer_pattern = load_protocol("protocol.xml")

# Simülasyon döngüsü
while True:
    status_list = []
    proto_results = []

    for i in range(8):
        device_id = f"DEV:{i+1:02d}"
        feed = FEED_KEYS[i]
        kat = PARK_KATLARI[feed]

        temp = round(random.uniform(18, 35), 1)
        hum = round(random.uniform(25, 70), 1)

        if random.random() < 0.15:
            status = "HATALI VERİ"
        else:
            status = random.choice(["DOLU", "BOŞ"])

        status_list.append(status)

        msg = f"{device_id};TEMP:{temp};HUM:{hum};FLOOR:{kat};SLOT:{i+1}#"

        valid_proto, proto_msg = validate_message(msg, header_pattern, body_patterns, footer_pattern)
        proto_results.append(valid_proto)

        if status != "HATALI VERİ" and valid_proto:
            print(f"GÖNDERİLİYOR: {device_id} - {msg}")
            client.publish(feed, msg)
            log_message_xml(device_id, msg, True)
        else:
            print(f"HATALI: {device_id} - {msg} ({proto_msg})")
            log_message_xml(device_id, f"{msg} ({proto_msg})", False)

    # DFA analiz
    if all(s != "HATALI VERİ" for s in status_list):
        is_valid, dfa_msg = dfa_validate_floors(status_list)
        print("\n[DFA] Durumlar:", status_list)
        print("[DFA] Mesaj:", dfa_msg)
        log_message_xml("SİSTEM", dfa_msg, is_valid)
    else:
        print("\n[DFA] Geçersiz veriler tespit edildi, DFA çalıştırılmadı.")

    print("="*40)
    time.sleep(5)
