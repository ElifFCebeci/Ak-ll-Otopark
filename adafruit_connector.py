from Adafruit_IO import MQTTClient
import time

ADAFRUIT_IO_USERNAME = "Elif19"
ADAFRUIT_IO_KEY = "aio_cfPa32MhI58OmHsfScUDmBUKYJof"

# Feed key'leri
FEED_SLOT1 = "1-park-alaninin-durumu"
FEED_SLOT2 = "2-park-alaninin-durumu"
FEED_STATUS = "genel-sistem-durumu"

# Bağlantı kurulduğunda çalışır
def connected(client):
    print("✅ MQTT bağlantısı kuruldu.")
    client.subscribe(FEED_SLOT1)
    client.subscribe(FEED_SLOT2)
    client.subscribe(FEED_STATUS)

# Mesaj geldiğinde çalışır
def message(client, feed_id, payload):
    print(f"📨 Feed: {feed_id} | İçerik: {payload}")

# MQTT istemcisi oluşturuluyor
client = MQTTClient(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
client.on_connect = connected
client.on_message = message

# Bağlantıyı başlat
client.connect()
client.loop_background()

#  Örnek veri gönderimi
while True:
    # Buraya gerçek sistemden gelen veriler de yazılabilir
    client.publish(FEED_SLOT1, "DOLU")
    client.publish(FEED_SLOT2, "BOŞ")
    client.publish(FEED_STATUS, "AKTİF")

    print(" Veriler Adafruit IO'ya gönderildi.")
    time.sleep(10)
