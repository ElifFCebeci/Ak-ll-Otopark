import xml.etree.ElementTree as ET
import random
from datetime import datetime

# XML'den verileri oku
tree = ET.parse('protocol.xml')
root = tree.getroot()

# Header
device_no = random.randint(1, 99)
header = f"DEV:{device_no};"

# Body
body_parts = []
for field in root.find(".//body").findall("field"):
    name = field.get("name")
    
    if name == "FLOOR":
        body_parts.append(f"FLOOR:{random.randint(1, 10)};")
    elif name == "SLOT":
        body_parts.append(f"SLOT:{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(1, 20)};")
    elif name == "STATUS":
        body_parts.append(f"STATUS:{random.choice(['DOLU', 'BOŞ'])};")
    elif name == "DATE":
        body_parts.append(f"DATE:{datetime.now().strftime('%Y-%m-%d')};")
    elif name == "TIME":
        body_parts.append(f"TIME:{datetime.now().strftime('%H:%M:%S')};")

# Footer
footer = "#"

# Tüm parçaları BİR BOŞLUKLA birleştir
sample_message = " ".join([header, *body_parts, footer])  # <-- Bu satır değişti!
print("ÜRETİLEN ÖRNEK MESAJ:")
print(sample_message)
