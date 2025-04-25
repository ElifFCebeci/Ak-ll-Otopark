import re
import random
import keyboard
import time
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from Adafruit_IO import MQTTClient

# Adafruit IO Bilgileri
ADAFRUIT_IO_USERNAME = "Elif19"
ADAFRUIT_IO_KEY = "aio_cfPa32MhI58OmHsfScUDmBUKYJof"
FEED_KEYS = ["1-park-alaninin-durumu", "2-park-alaninin-durumu",
             "3-park-alaninin-durumu", "4-park-alaninin-durumu",
             "5-park-alaninin-durumu", "6-park-alaninin-durumu",
             "7-park-alaninin-durumu", "8-park-alaninin-durumu"]

# Park Alanları Kat Bilgisi
PARK_KATLARI = {key: 1 if i < 4 else 2 for i, key in enumerate(FEED_KEYS)}

# XML Protokol Yükleme
def load_protocol(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    header_pattern = root.find('./message/header').attrib['pattern']
    body_fields = root.findall('./message/body/field')
    body_patterns = [f.attrib['pattern'] for f in body_fields]
    footer_pattern = root.find('./message/footer').attrib['pattern']

    return header_pattern, body_patterns, footer_pattern

# Mesaj Doğrulama
def validate_message(message, header_pattern, body_patterns, footer_pattern):
    pos = 0
    header_match = re.match(header_pattern, message[pos:])
    if not header_match:
        return False, " Header hatalı"
    pos += header_match.end()

    for pattern in body_patterns:
        match = re.match(pattern, message[pos:])
        if not match:
            return False, f" Body hatalı: {pattern}"
        pos += match.end()

    footer_match = re.match(footer_pattern, message[pos:])
    if not footer_match:
        return False, " Footer hatalı"
    pos += footer_match.end()

    return pos == len(message), " Mesaj geçerli"

# Loglama (Sadece geçersiz mesajlar kaydedilecek)
def log_message_xml(device, message, is_valid):
    if is_valid:  # Eğer mesaj geçerliyse loga ekleme yapma
        return

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
    ET.SubElement(log_entry, "timestamp").text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ET.SubElement(log_entry, "device").text = device
    ET.SubElement(log_entry, "status").text = "Geçersiz"
    ET.SubElement(log_entry, "message").text = message

    tree.write(log_file_path, encoding="utf-8", xml_declaration=True)

# MQTT Bağlantısı
def connected(client):
    print("Bağlantı başarılı!")

client = MQTTClient(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
client.on_connect = connected
client.connect()
client.loop_background()

# XML protokolü yükle
header_pattern, body_patterns, footer_pattern = load_protocol("protocoll.xml")

try:
    while True:
        if keyboard.is_pressed('q'):  # Kullanıcı "q" tuşuna bastığında çıkış yap
            print("Kullanıcı çıkış yaptı. Simülasyon durduruluyor.")
            break

        for i in range(8):
            device_id = f"DEV:{i+1:02d}"
            kat = PARK_KATLARI[FEED_KEYS[i]]
            status = "HATALI VERİ" if random.random() < 0.15 else random.choice(["DOLU", "BOŞ"])
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            mesaj = f"{device_id}; FLOOR:{kat}; SLOT:A{i+1}; STATUS:{status}; DATE:{timestamp[:10]}; TIME:{timestamp[11:]}; #"

            is_valid, validation_msg = validate_message(mesaj, header_pattern, body_patterns, footer_pattern)

            if is_valid:
                print(f"✅ Geçerli mesaj: {mesaj}")
                client.publish(FEED_KEYS[i], mesaj)
            else:
                print(f"❌ Geçersiz mesaj: {validation_msg}")
                log_message_xml(device_id, mesaj, is_valid)  # Sadece geçersiz mesajları kaydediyoruz!

        time.sleep(5)

except KeyboardInterrupt:
    print("Program manuel olarak durduruldu.")
