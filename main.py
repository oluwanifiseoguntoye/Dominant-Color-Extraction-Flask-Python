from flask import Flask, render_template, request, jsonify
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

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


def get_dominant_color(image, k=5):
    image = image.resize((150, 150))
    pixels = np.array(image).reshape(-1, 3)

    # Filter out black and white pixels
    pixels = pixels[(pixels[:, 0] > 20) | (pixels[:, 1] > 20) | (pixels[:, 2] > 20)]
    pixels = pixels[(pixels[:, 0] < 235) | (pixels[:, 1] < 235) | (pixels[:, 2] < 235)]

    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=k)
    kmeans.fit(pixels)
    colors = kmeans.cluster_centers_
    labels = kmeans.labels_

    # Count the frequency of each cluster
    counts = np.bincount(labels)

    # Select the most frequent cluster
    dominant_color = colors[np.argmax(counts)]
    return tuple(map(int, dominant_color))


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


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            image = Image.open(file)
            dominant_color_rgb = get_dominant_color(image)
            dominant_color_hex = rgb_to_hex(dominant_color_rgb)
            color_name = get_closest_color_name(dominant_color_hex)
            return jsonify({
                'hex_code': dominant_color_hex,
                'color_name': color_name
            })
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, port=5012)
