from Adafruit_IO import MQTTClient
import random
import time
from datetime import datetime
import xml.etree.ElementTree as ET
import os
ADAFRUIT_IO_USERNAME = "Elif19"
ADAFRUIT_IO_KEY = "aio_cfPa32MhI58OmHsfScUDmBUKYJof"
FEED_KEYS = ["1-park-alaninin-durumu", "2-park-alaninin-durumu"]

# MQTT bağlantısı
def connected(client):
    print("Connection successful!")

client = MQTTClient(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
client.on_connect = connected
client.connect()
client.loop_background()

# XML tabanlı log kaydı yapma fonksiyonu
def log_message_xml(device, message, is_valid):
    log_file_path = "simulator_log.xml"

    # Dosya varsa oku, yoksa yeni logs elementi oluştur
    if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > 0:
        try:
            tree = ET.parse(log_file_path)
            root = tree.getroot()
        except ET.ParseError:
            print("Bozul XML dosyası. Yeniden başlatılıyor.")
            root = ET.Element("logs")
            tree = ET.ElementTree(root)
    else:
        root = ET.Element("logs")
        tree = ET.ElementTree(root)

    # Yeni log girdisi
    log_entry = ET.SubElement(root, "log")

    timestamp = ET.SubElement(log_entry, "timestamp")
    timestamp.text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    device_element = ET.SubElement(log_entry, "device")
    device_element.text = device

    status = ET.SubElement(log_entry, "status")
    status.text = "Geçerli" if is_valid else "Geçersiz"

    message_element = ET.SubElement(log_entry, "message")
    message_element.text = message

    # Dosyayı tekrar yaz
    tree.write(log_file_path, encoding="utf-8", xml_declaration=True)
# DFA ile veri doğrulama fonksiyonu
def dfa_validate(status, temperature, humidity):
    state = "q0"

    if state == "q0":
        if status in ["DOLU", "BOŞ"]:
            state = "q1"
        else:
            return False

    if state == "q1":
        if 20.0 <= temperature <= 30.0:
            state = "q2"
        else:
            return False,"Temperature out of range"

    if state == "q2":
        if 30 <= humidity <= 65:
            state = "q3"
        else:
            return False,"Humidity out of range"

    if state == "q3":
        return True,"Geçerli veri"

    return False

# Başlangıç verileri
temperature = [25.0, 26.0]
humidity = [45, 50]

# Simülasyon döngüsü
while True:
    for i in range(2):
        device_id = f"DEV:0{i+1}"

        # Sıcaklık ve nem trende göre değişiyor
        temp_delta = random.uniform(-0.4, 0.4)
        temperature[i] = max(20.0, min(30.0, temperature[i] + temp_delta))

        hum_delta = random.randint(-2, 2)
        humidity[i] = max(30, min(65, humidity[i] + hum_delta))

        status = random.choice(["DOLU", "BOŞ"])
        # Sorunlu veri gönderimi,gerçek hayat ile uyumlu olmasını sağlar.
        if random.random() < 0.15:  # %15 ihtimalle hatalı veri gönder
            bad_msg = "Hatalı Veri"
            print(f"HATALI: {bad_msg}")
            client.publish(FEED_KEYS[i], bad_msg)
            log_message_xml(device_id, bad_msg, False)
        else:
            if dfa_validate(status, temperature[i], humidity[i]):
                good_msg = f"{status}"
                print(f"Geçerli: {good_msg}")
                client.publish(FEED_KEYS[i], good_msg)
                log_message_xml(device_id, good_msg, True)
            else:
                print(f"Geçersiz veri - tekrar gönderilmiyor: {device_id}")
                log_message_xml(device_id, f"{status}/{temperature[i]}/{humidity[i]}", False)

    time.sleep(7) 