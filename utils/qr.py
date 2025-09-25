# utils/qr.py
import qrcode
from PIL import Image
import io

def generate_qr_code(data):
    qr = qrcode.make(data)
    img = Image.open(io.BytesIO(qr.png()))
    return img
