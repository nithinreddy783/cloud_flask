import os
import cv2
import numpy as np
import random
import shutil
from flask import Blueprint, current_app, render_template, redirect, request, flash
from werkzeug.utils import secure_filename

image = Blueprint("image", __name__, static_folder="static",
                  template_folder="templates")

def mod_inverse(a, m):
    m0, x0, x1 = m, 0, 1
    if m == 1:
        return 0
    while a > 1:
        q = a // m
        m, a = a % m, m
        x0, x1 = x1 - q * x0, x0
    if x1 < 0:
        x1 += m0
    return x1

def generate_keys():
    p = 104729  # A prime number
    g = 2  # Primitive root modulo of p
    x = random.randint(1, p-2)  # Private key x
    y = pow(g, x, p)  # y = g^x mod p, Public Key
    return (p, g, y), x

def encrypt_message(public_key, plaintext):
    p, g, y = public_key
    k = random.randint(1, p-2)  # Random number for each encryption
    a = pow(g, k, p)  # a = g^k mod p
    b = [(ord(char) * pow(y, k, p)) % p for char in plaintext]  # b = M * y^k mod p for each character
    return a, b

def decrypt_message(private_key, a, b, p):
    x = private_key
    a_inv = mod_inverse(pow(a, x, p), p)  # a^-x mod p
    plaintext = ''.join([chr((char * a_inv) % p) for char in b])
    return plaintext

public_key, private_key = generate_keys()

@image.route("/encode")
def image_encode():
    if os.path.exists(current_app.config['IMAGE_CACHE_FOLDER']):
        shutil.rmtree(current_app.config['IMAGE_CACHE_FOLDER'], ignore_errors=True)
    if os.path.exists(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "adjusted_sample.jpg")):
        os.remove(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "adjusted_sample.jpg"))
    if os.path.exists(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "encrypted_image.png")):
        os.remove(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "encrypted_image.png"))

    return render_template("encode-image.html")

@image.route("/encode-result", methods=['POST', 'GET'])
def image_encode_result():
    if request.method == 'POST':
        message = request.form['message']
        if 'image' not in request.files or request.files['image'].filename == '':
            flash('No image selected')
            return redirect(request.url)

        file = request.files['image']
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], filename)
        file.save(file_path)

        a, b = encrypt_message(public_key, message)
        encrypted_message = f"{a} " + ' '.join(map(str, b))

        encrypt_image(file_path, message)

        return render_template("encode-result.html", file=file, encryption=True, message=message, encrypted_message=encrypted_message)

@image.route("/decode")
def image_decode():
    if os.path.exists(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "decrypted_sample.png")):
        os.remove(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "decrypted_sample.png"))
    if os.path.exists(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "decrypted_secret.png")):
        os.remove(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "decrypted_secret.png"))

    return render_template("decode-image.html")

@image.route("/decode-result", methods=['POST', 'GET'])
def image_decode_result():
    if request.method == 'POST':
        if 'image' not in request.files or request.files['image'].filename == '':
            flash('No image selected')
            return redirect(request.url)

        file = request.files['image']
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], filename)
        file.save(file_path)

        decrypted_message = decrypt_image(file_path)

        return render_template("decode-result.html", file=file, decryption=True, decrypted_message=decrypted_message)

def encrypt_image(image_path, message):
    img2 = cv2.imread(image_path)
    dimensions = img2.shape

    sample_image_path = os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "sample.jpg")
    adjusted_sample_image = cv2.imread(sample_image_path).copy()
    adjusted_sample_image = cv2.resize(adjusted_sample_image, (dimensions[1], dimensions[0]))
    adjusted_sample_path = os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "adjusted_sample.jpg")
    cv2.imwrite(adjusted_sample_path, adjusted_sample_image)
    img1 = cv2.imread(adjusted_sample_path)

    for i in range(img2.shape[0]):
        for j in range(img2.shape[1]):
            for l in range(3):
                v1 = format(img1[i][j][l], '08b')
                v2 = format(img2[i][j][l], '08b')
                v3 = v1[:4] + v2[:4]
                img1[i][j][l] = int(v3, 2)

    encrypted_image_path = os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "encrypted_image.png")
    cv2.imwrite(encrypted_image_path, img1)

def decrypt_image(image_path):
    img = cv2.imread(image_path)
    width, height, _ = img.shape

    img1 = np.zeros((width, height, 3), np.uint8)
    img2 = np.zeros((width, height, 3), np.uint8)

    for i in range(width):
        for j in range(height):
            for l in range(3):
                v1 = format(img[i][j][l], '08b')
                v2 = v1[:4] + chr(random.randint(0, 1) + 48) * 4
                v3 = v1[4:] + chr(random.randint(0, 1) + 48) * 4
                img1[i][j][l] = int(v2, 2)
                img2[i][j][l] = int(v3, 2)

    decrypted_sample_path = os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "decrypted_sample.png")
    decrypted_secret_path = os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "decrypted_secret.png")
    cv2.imwrite(decrypted_sample_path, img1)
    cv2.imwrite(decrypted_secret_path, img2)

    return "Decrypted messages are saved."
