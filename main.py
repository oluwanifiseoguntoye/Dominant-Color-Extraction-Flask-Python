from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from sklearn.cluster import KMeans
import pdfkit
import io
import os

app = Flask(__name__)

# Define a list of color names and their corresponding RGB values
color_names = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    "pink": (255, 192, 203),
    "brown": (165, 42, 42),
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "gray": (128, 128, 128),
}

def get_color_palette(image, k=5):
    image = image.resize((150, 150))
    pixels = np.array(image).reshape(-1, 3)

    # Filter out black and white pixels
    pixels = pixels[(pixels[:, 0] > 20) | (pixels[:, 1] > 20) | (pixels[:, 2] > 20)]
    pixels = pixels[(pixels[:, 0] < 235) | (pixels[:, 1] < 235) | (pixels[:, 2] < 235)]

    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=k)
    kmeans.fit(pixels)
    colors = kmeans.cluster_centers_

    return [tuple(map(int, color)) for color in colors]

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i + 2], 16) for i in (0, 2, 4))

def get_closest_color_name(hex_code):
    rgb = hex_to_rgb(hex_code)
    min_distance = float('inf')
    closest_color = ""
    for name, color_rgb in color_names.items():
        distance = np.linalg.norm(np.array(rgb) - np.array(color_rgb))
        if distance < min_distance:
            min_distance = distance
            closest_color = name
    return closest_color

def generate_color_palette_image(colors):
    width, height = 500, 100
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    for i, color in enumerate(colors):
        hex_code = color['hex_code']
        color_name = color['color_name']
        rect_width = width // len(colors)
        draw.rectangle([i * rect_width, 0, (i + 1) * rect_width, height], fill=hex_code)
        draw.text((i * rect_width + 10, height - 20), f"{color_name}\n{hex_code}", fill=(0, 0, 0), font=font)

    return image

def generate_pdf_report(colors, image_path):
    html_content = f"""
    <html>
    <head>
        <title>Color Palette Report</title>
    </head>
    <body>
        <h1>Color Palette Report</h1>
        <img src="{image_path}" alt="Color Palette">
        <ul>
    """
    for color in colors:
        html_content += f"<li>{color['color_name']} - {color['hex_code']}</li>"
    html_content += "</ul></body></html>"

    pdfkit.from_string(html_content, 'report.pdf')
    return 'report.pdf'

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        x = int(request.form['x'])
        y = int(request.form['y'])
        width = int(request.form['width'])
        height = int(request.form['height'])

        if file:
            image = Image.open(file)
            cropped_image = image.crop((x, y, x + width, y + height))
            color_palette_rgb = get_color_palette(cropped_image)
            color_palette_hex = [rgb_to_hex(color) for color in color_palette_rgb]
            color_names_list = [get_closest_color_name(hex_code) for hex_code in color_palette_hex]
            colors = [{'hex_code': hex_code, 'color_name': color_name} for hex_code, color_name in zip(color_palette_hex, color_names_list)]

            # Generate color palette image
            palette_image = generate_color_palette_image(colors)
            palette_image_path = 'palette.png'
            palette_image.save(palette_image_path)

            # Generate PDF report
            pdf_report_path = generate_pdf_report(colors, palette_image_path)

            return jsonify({
                'colors': colors,
                'palette_image_path': palette_image_path,
                'pdf_report_path': pdf_report_path
            })
    return render_template('index.html')

@app.route('/download/<file_type>', methods=['GET'])
def download_file(file_type):
    if file_type == 'image':
        return send_file('palette.png', as_attachment=True)
    elif file_type == 'report':
        return send_file('report.pdf', as_attachment=True)
    else:
        return "Invalid file type", 400

if __name__ == '__main__':
    app.run(debug=True, port=5012)