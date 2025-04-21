import xml.etree.ElementTree as ET
from Adafruit_IO import MQTTClient

# Adafruit MQTT Ayarları
ADAFRUIT_IO_USERNAME = "Elif19"
ADAFRUIT_IO_KEY = "aio_cfPa32MhI58OmHsfScUDmBUKYJof"
FEED_KEYS = [
    "1-park-alaninin-durumu", "2-park-alaninin-durumu",
    "3-park-alaninin-durumu", "4-park-alaninin-durumu",
    "5-park-alaninin-durumu", "6-park-alaninin-durumu",
    "7-park-alaninin-durumu", "8-park-alaninin-durumu"
]

# MQTT bağlantısı
def connected(client):
    print("Bağlantı başarılı!")

client = MQTTClient(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
client.on_connect = connected
client.connect()
client.loop_background()

# XML Dosyasından Park Yeri Durumlarını Okuma
def read_park_yeri_durumlari(xml_dosya):
    tree = ET.parse(xml_dosya)
    root = tree.getroot()

    park_yeri_durumlari = []

    for yer in root.findall('yer'):
        konum = yer.find('konum').text
        durum = yer.find('durum').text
        park_yeri_durumlari.append((konum, durum))

    return park_yeri_durumlari

# Veriyi XML'den alıp Adafruit Feed'lerine Gönderme
def gonder_park_yeri_durumlarini():
    # XML dosyasından park yeri durumlarını al
    park_yeri_durumlari = read_park_yeri_durumlari("park_yerleri.xml")

    # Durumları Adafruit Feed'lerine gönder
    for konum, durum in park_yeri_durumlari:
        if konum in FEED_KEYS:
            print(f"GÖNDERİLİYOR: {konum} - Durum: {durum}")
            client.publish(konum, durum)  # Durumu ilgili feed'e gönder
        else:
            print(f"Geçersiz konum: {konum}")

# Ana döngü
if __name__ == "__main__":
    gonder_park_yeri_durumlarini()  # Park yerleri durumlarını gönder
