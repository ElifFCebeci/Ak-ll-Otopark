import re
import xml.etree.ElementTree as ET

def load_protocol(filename):
    """XML dosyasından protokol kurallarını yükler"""
    tree = ET.parse(filename)
    root = tree.getroot()

    header_pattern = root.find('./message/header').attrib['pattern']
    body_fields = root.findall('./message/body/field')
    body_patterns = [f.attrib['pattern'] for f in body_fields]
    footer_pattern = root.find('./message/footer').attrib['pattern']

    return header_pattern, body_patterns, footer_pattern

def validate_message(message, header_pattern, body_patterns, footer_pattern):
    """Bir mesajın XML kurallarına göre geçerli olup olmadığını kontrol eder"""
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

    if pos != len(message):
        return False, " Fazla veri var"

    return True, " Mesaj geçerli"

# Test
if __name__ == "__main__":
    protocol = load_protocol("protocol.xml")
    test_msg = "DEV:3;TEMP:25.2;HUM:40.0;FLOOR:2;SLOT:5#"
    result, explanation = validate_message(test_msg, *protocol)
    print("Sonuç:", explanation)
