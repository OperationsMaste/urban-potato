# utils.py
import qrcode
from PIL import Image, ImageDraw, ImageFont
import io

def generate_qr_bytes(text: str):
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

def create_ticket_image(event_title, name, qr_bytes):
    from PIL import ImageFont
    buf_qr = io.BytesIO(qr_bytes)
    qr_img = Image.open(buf_qr).convert("RGBA")

    w, h = 900, 350
    base = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(base)

    try:
        title_font = ImageFont.truetype("arial.ttf", 28)
        big_font = ImageFont.truetype("arial.ttf", 40)
        small_font = ImageFont.truetype("arial.ttf", 18)
    except:
        title_font = ImageFont.load_default()
        big_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    draw.text((30, 30), "Inter-College Fest", font=title_font, fill=(30,30,30))
    draw.text((30, 80), event_title, font=big_font, fill=(10,10,10))
    draw.text((30, 150), f"Ticket for: {name}", font=small_font, fill=(50,50,50))
    draw.text((30, 180), "Entry: Present this ticket and QR code at entry.", font=small_font, fill=(80,80,80))

    qr_scaled = qr_img.resize((200, 200))
    base.paste(qr_scaled, (650, 70), qr_scaled)

    out = io.BytesIO()
    base.convert("RGB").save(out, format="PNG")
    out.seek(0)
    return out.getvalue()

def local_css():
    css = """
    <style>
    .card {
        background: linear-gradient(180deg, #ffffff 0%, #f6f9ff 100%);
        padding: 14px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(20,20,60,0.08);
        margin-bottom: 12px;
    }
    .event-title { font-size:18px; font-weight:600; margin-bottom:6px; }
    .muted { color:#666; font-size:13px; }
    </style>
    """
    try:
        import streamlit as st
        st.markdown(css, unsafe_allow_html=True)
    except Exception:
        pass
