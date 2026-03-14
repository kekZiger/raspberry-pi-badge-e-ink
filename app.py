import os
import sys
import sqlite3
import base64
from io import BytesIO
from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageDraw, ImageFont

sys.path.append('/home/badge/e-Paper/RaspberryPi_JetsonNano/python/lib')
from waveshare_epd import epd2in13_V3

app = Flask(__name__)

EPD_WIDTH  = 250
EPD_HEIGHT = 122
DB_PATH    = '/home/badge/badge-app/badges.db'
FONTS_DIR  = '/home/badge/badge-app/fonts'
UPLOAD_DIR = '/home/badge/badge-app/static/uploads'

os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Datenbank ---

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS badges (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT,
                title     TEXT,
                info      TEXT,
                rotation  INTEGER DEFAULT 0,
                image     TEXT,
                created   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

# --- Bild-Verarbeitung ---

def process_image(file) -> str | None:
    if not file or file.filename == '':
        return None
    img = Image.open(file)
    img = img.convert('L')
    img.thumbnail((60, 60), Image.LANCZOS)
    img = img.convert('1')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

# --- Rendering (shared zwischen Display und Preview) ---

def build_image(name: str, title: str, info: str, rotation: int, image_b64: str | None) -> Image.Image:
    if rotation in (90, 270):
        canvas_w, canvas_h = EPD_HEIGHT, EPD_WIDTH
    else:
        canvas_w, canvas_h = EPD_WIDTH, EPD_HEIGHT

    image = Image.new('1', (canvas_w, canvas_h), 255)
    draw  = ImageDraw.Draw(image)

    font_large  = ImageFont.truetype(f'{FONTS_DIR}/DejaVuSans-Bold.ttf', 24)
    font_medium = ImageFont.truetype(f'{FONTS_DIR}/DejaVuSans.ttf', 14)
    font_small  = ImageFont.truetype(f'{FONTS_DIR}/DejaVuSans.ttf', 11)

    text_x = 10

    if image_b64:
        img_data  = base64.b64decode(image_b64)
        badge_img = Image.open(BytesIO(img_data))
        image.paste(badge_img, (10, 10))
        text_x = 80

    draw.text((text_x, 8),  name,  font=font_large,  fill=0)
    draw.line([(text_x, 38), (canvas_w - 10, 38)], fill=0, width=1)
    draw.text((text_x, 42), title, font=font_medium, fill=0)
    draw.text((text_x, 62), info,  font=font_small,  fill=0)

    if rotation != 0:
        image = image.rotate(rotation, expand=True)

    return image

def render_to_display(name: str, title: str, info: str, rotation: int, image_b64: str | None):
    image = build_image(name, title, info, rotation, image_b64)
    epd   = epd2in13_V3.EPD()
    epd.init()
    epd.Clear(0xFF)
    epd.display(epd.getbuffer(image))
    epd.sleep()

def generate_preview(name: str, title: str, info: str, rotation: int, image_b64: str | None) -> str:
    image = build_image(name, title, info, rotation, image_b64)
    if rotation in (90, 270):
        w, h = EPD_HEIGHT, EPD_WIDTH
    else:
        w, h = EPD_WIDTH, EPD_HEIGHT
    image = image.resize((w * 4, h * 4), Image.NEAREST)
    image = image.convert('RGB')
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

# --- Routen ---

@app.route('/')
def index():
    with get_db() as conn:
        badges = conn.execute('SELECT * FROM badges ORDER BY created DESC').fetchall()
    return render_template('index.html', badges=badges)

@app.route('/save', methods=['POST'])
def save():
    name      = request.form.get('name', '')
    title     = request.form.get('title', '')
    info      = request.form.get('info', '')
    rotation  = int(request.form.get('rotation', 0))
    image_b64 = None

    if 'image' in request.files:
        image_b64 = process_image(request.files['image'])

    with get_db() as conn:
        cursor = conn.execute(
            'INSERT INTO badges (name, title, info, rotation, image) VALUES (?, ?, ?, ?, ?)',
            (name, title, info, rotation, image_b64)
        )
        new_id = cursor.lastrowid

    return jsonify({'status': 'ok', 'id': new_id, 'name': name, 'title': title, 'info': info, 'rotation': rotation})

@app.route('/update/<int:badge_id>', methods=['POST'])
def update(badge_id):
    name     = request.form.get('name', '')
    title    = request.form.get('title', '')
    info     = request.form.get('info', '')
    rotation = int(request.form.get('rotation', 0))

    with get_db() as conn:
        existing  = conn.execute('SELECT image FROM badges WHERE id = ?', (badge_id,)).fetchone()
        image_b64 = existing['image'] if existing else None

        if 'image' in request.files and request.files['image'].filename != '':
            image_b64 = process_image(request.files['image'])

        conn.execute(
            'UPDATE badges SET name=?, title=?, info=?, rotation=?, image=? WHERE id=?',
            (name, title, info, rotation, image_b64, badge_id)
        )

    return jsonify({'status': 'ok'})

@app.route('/display/<int:badge_id>', methods=['POST'])
def display(badge_id):
    with get_db() as conn:
        badge = conn.execute('SELECT * FROM badges WHERE id = ?', (badge_id,)).fetchone()
    if not badge:
        return jsonify({'status': 'error', 'message': 'Nicht gefunden'}), 404

    render_to_display(badge['name'], badge['title'], badge['info'], badge['rotation'], badge['image'])
    return jsonify({'status': 'ok'})

@app.route('/preview', methods=['POST'])
def preview():
    name      = request.form.get('name', '')
    title     = request.form.get('title', '')
    info      = request.form.get('info', '')
    rotation  = int(request.form.get('rotation', 0))
    image_b64 = None

    if 'image' in request.files and request.files['image'].filename != '':
        image_b64 = process_image(request.files['image'])

    preview_b64 = generate_preview(name, title, info, rotation, image_b64)
    return jsonify({'preview': preview_b64})

@app.route('/delete/<int:badge_id>', methods=['DELETE'])
def delete(badge_id):
    with get_db() as conn:
        conn.execute('DELETE FROM badges WHERE id = ?', (badge_id,))
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
