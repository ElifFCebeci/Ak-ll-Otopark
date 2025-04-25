import tkinter as tk
from tkinter import ttk
from Adafruit_IO import MQTTClient
import time
from datetime import datetime
import re

ADAFRUIT_AIO_USERNAME = "Elif19"
ADAFRUIT_AIO_KEY = "aio_cfPa32MhI58OmHsfScUDmBUKYJof"
FEED_KEYS = [
    "1-park-alaninin-durumu", "2-park-alaninin-durumu",
    "3-park-alaninin-durumu", "4-park-alaninin-durumu",
    "5-park-alaninin-durumu", "6-park-alaninin-durumu",
    "7-park-alaninin-durumu", "8-park-alaninin-durumu"
]

root = tk.Tk()
root.title("Park Alanı Durumu")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}")

stil = ttk.Style()
stil.configure("KatCercevesi.TLabelframe", background="dimgray")
stil.configure("KatCercevesi.TLabelframe.Label", background="lightgray")

park_durumlari = {}
renkler = {}
park_gostergeleri = {}
park_bilgileri = {}
for i, feed in enumerate(FEED_KEYS):
    park_durumlari[feed] = tk.StringVar(value="Bekleniyor...")
    renkler[feed] = tk.StringVar(value="lightgray")
    kat = 1 if i < 4 else 2
    park_no = i % 4 + 1
    park_bilgileri[feed] = {"kat": kat, "no": park_no}

kat_bos_dolu_sayilari = {1: {"bos": tk.IntVar(value=0), "dolu": tk.IntVar(value=0)},
                        2: {"bos": tk.IntVar(value=0), "dolu": tk.IntVar(value=0)}}
kat_sayi_etiketleri = {}

mqtt_mesajlari = []
mqtt_mesaj_metni = tk.StringVar()

def log_mqtt_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mqtt_mesajlari.append(f"[{timestamp}] {message}")
    if len(mqtt_mesajlari) > 10:
        mqtt_mesajlari.pop(0)
    mqtt_mesaj_metni.set("\n".join(mqtt_mesajlari))

client = MQTTClient(ADAFRUIT_AIO_USERNAME, ADAFRUIT_AIO_KEY)

def connected(client):
    print("Adafruit IO'ya bağlanıldı!")
    log_mqtt_message("Adafruit IO'ya bağlanıldı!")
    for feed in FEED_KEYS:
        client.subscribe(feed)
    guncelle_baslangic_sayilari()

def guncelle_baslangic_sayilari():
    for feed in FEED_KEYS:
        kat = park_bilgileri[feed]["kat"]
        durum_mesaji = park_durumlari[feed].get()
        match = re.search(r"STATUS:(DOLU|BOŞ)", durum_mesaji)
        if match:
            durum = match.group(1)
            if durum == "BOŞ":
                kat_bos_dolu_sayilari[kat]["bos"].set(kat_bos_dolu_sayilari[kat]["bos"].get() + 1)
            elif durum == "DOLU":
                kat_bos_dolu_sayilari[kat]["dolu"].set(kat_bos_dolu_sayilari[kat]["dolu"].get() + 1)
    guncelle_kat_sayi_etiketleri()

def disconnected(client):
    print("Adafruit IO bağlantısı kesildi!")
    log_mqtt_message("Adafruit IO bağlantısı kesildi!")

def message(client, feed_id, payload):
    mesaj = f"Gelen: Feed={feed_id}, Değer={payload}"
    print(mesaj)
    log_mqtt_message(mesaj)

    if feed_id in park_durumlari:
        onceki_durum = park_durumlari[feed_id].get()
        try:
            match = re.match(r"DEV:\d+; FLOOR:(\d+); SLOT:A(\d+); STATUS:(DOLU|BOŞ); DATE:.*; TIME:.*; #", payload)
            if match:
                kat = int(match.group(1))
                slot = int(match.group(2))
                durum = match.group(3)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                park_durumlari[feed_id].set(f"{kat}. Kat - {slot}. Park: {durum} (Alındı: {timestamp})")

                if durum == "BOŞ":
                    renkler[feed_id].set("forestgreen")
                    onceki_durum_match = re.search(r"STATUS:(DOLU|BOŞ)", onceki_durum)
                    if onceki_durum_match and onceki_durum_match.group(1) == "DOLU":
                        kat_bos_dolu_sayilari[kat]["dolu"].set(kat_bos_dolu_sayilari[kat]["dolu"].get() - 1)
                        kat_bos_dolu_sayilari[kat]["bos"].set(kat_bos_dolu_sayilari[kat]["bos"].get() + 1)
                    elif "Bekleniyor" in onceki_durum:
                        kat_bos_dolu_sayilari[kat]["bos"].set(kat_bos_dolu_sayilari[kat]["bos"].get() + 1)
                elif durum == "DOLU":
                    renkler[feed_id].set("firebrick")
                    onceki_durum_match = re.search(r"STATUS:(DOLU|BOŞ)", onceki_durum)
                    if onceki_durum_match and onceki_durum_match.group(1) == "BOŞ":
                        kat_bos_dolu_sayilari[kat]["dolu"].set(kat_bos_dolu_sayilari[kat]["dolu"].get() + 1)
                        kat_bos_dolu_sayilari[kat]["bos"].set(kat_bos_dolu_sayilari[kat]["bos"].get() - 1)
                    elif "Bekleniyor" in onceki_durum:
                        kat_bos_dolu_sayilari[kat]["dolu"].set(kat_bos_dolu_sayilari[kat]["dolu"].get() + 1)
                else:
                    renkler[feed_id].set("goldenrod")

                guncelle_renkler()
                guncelle_kat_sayi_etiketleri()
            else:
                log_mqtt_message(f"Hatalı formatta mesaj alındı: {payload}")
        except Exception as e:
            print(f"Payload işleme hatası: {e}, Payload: {payload}")

def guncelle_renkler():
    for feed, renk_degiskeni in renkler.items():
        if feed in park_gostergeleri and "gosterge" in park_gostergeleri[feed]:
            park_gostergeleri[feed]["gosterge"].itemconfig(1, fill=renk_degiskeni.get())

def guncelle_kat_sayi_etiketleri():
    for kat, sayilar in kat_bos_dolu_sayilari.items():
        if kat in kat_sayi_etiketleri:
            kat_sayi_etiketleri[kat]["bos"].config(text=f"Boş: {sayilar['bos'].get()}")
            kat_sayi_etiketleri[kat]["dolu"].config(text=f"Dolu: {sayilar['dolu'].get()}")

client.on_connect = connected
client.on_disconnect = disconnected
client.on_message = message

client.connect()
client.loop_background()

sol_frame = ttk.Frame(root, padding=10)
sol_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

for kat_no in sorted(set(park_bilgileri[key]["kat"] for key in FEED_KEYS)):
    kat_cercevesi = ttk.LabelFrame(sol_frame, text=f"{kat_no}. Kat", padding=10, style="KatCercevesi.TLabelframe")
    kat_cercevesi.pack(pady=10, padx=10, fill="x")

    kat_bilgi_cercevesi = ttk.Frame(kat_cercevesi, padding=5)
    kat_bilgi_cercevesi.pack(fill="x", pady=5)

    kat_baslik = ttk.Label(kat_bilgi_cercevesi, text=f"{kat_no}. Kat:", font=("Arial", 12, "bold"))
    kat_baslik.pack(side=tk.LEFT)

    bos_etiketi = ttk.Label(kat_bilgi_cercevesi, text=f"Boş: {kat_bos_dolu_sayilari[kat_no]['bos'].get()}", font=("Arial", 10))
    bos_etiketi.pack(side=tk.LEFT, padx=5)
    dolu_etiketi = ttk.Label(kat_bilgi_cercevesi, text=f"Dolu: {kat_bos_dolu_sayilari[kat_no]['dolu'].get()}", font=("Arial", 10))
    dolu_etiketi.pack(side=tk.LEFT, padx=5)
    kat_sayi_etiketleri[kat_no] = {"bos": bos_etiketi, "dolu": dolu_etiketi}

    park_alani_cercevesi = ttk.Frame(kat_cercevesi, padding=5)
    park_alani_cercevesi.pack(fill="x")
    park_alani_cercevesi.grid_columnconfigure(0, weight=1)
    park_alani_cercevesi.grid_columnconfigure(1, weight=1)

    for i, feed in enumerate(FEED_KEYS):
        if park_bilgileri[feed]["kat"] == kat_no:
            park_cercevesi = ttk.Frame(park_alani_cercevesi, padding=5)
            column = (park_bilgileri[feed]["no"] - 1) % 2
            park_cercevesi.grid(row=(park_bilgileri[feed]["no"] - 1) // 2, column=column, padx=5, pady=2, sticky="ew")

            park_no = park_bilgileri[feed]["no"]
            etiket_baslik = ttk.Label(park_cercevesi, text=f"P{park_no}", font=("Arial", 10, "bold"))
            etiket_baslik.pack()

            gosterge = tk.Canvas(park_cercevesi, width=30, height=30, bg="lightgray", highlightthickness=0)
            gosterge.pack(pady=2)
            gosterge.create_rectangle(2, 2, 28, 28, fill=renkler[feed].get())
            park_gostergeleri[feed] = {"cerceve": park_cercevesi, "gosterge": gosterge}

sag_frame = ttk.LabelFrame(root, text="MQTT Mesajları", padding=10)
sag_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
sag_frame.grid_rowconfigure(0, weight=1)
sag_frame.grid_columnconfigure(0, weight=1)

mesaj_alani = tk.Text(sag_frame, height=15, width=40, state=tk.DISABLED)
mesaj_alani.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

def mesajlari_guncelle():
    mesaj_alani.config(state=tk.NORMAL)
    mesaj_alani.delete("1.0", tk.END)
    mesaj_alani.insert(tk.END, mqtt_mesaj_metni.get())
    mesaj_alani.config(state=tk.DISABLED)
    root.after(100, mesajlari_guncelle)

root.after(100, mesajlari_guncelle)

root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)

root.mainloop()