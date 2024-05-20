import os
import shutil
import wave
from flask import Blueprint, current_app, render_template, url_for, redirect, request, session, flash
from datetime import timedelta
from werkzeug.utils import secure_filename
import random

audio = Blueprint("audio", __name__, static_folder="static",
                  template_folder="templates")

def gcd_extended(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        gcd, x, y = gcd_extended(b % a, a)
        return (gcd, y - (b // a) * x, x)

def mod_inverse(a, m):
    gcd, x, _ = gcd_extended(a, m)
    if gcd != 1:
        raise ValueError("Inverse does not exist")
    else:
        return x % m

def generate_keys():
    # Using a large prime number for the modulus
    p = 104729  # A prime number
    g = 2  # Primitive root modulo of p
    x = random.randint(1, p-2)  # Private key x
    y = pow(g, x, p)  # y = g^x mod p, Public Key
    return (p, g, y), x

def encrypt(public_key, plaintext):
    p, g, y = public_key
    k = random.randint(1, p-2)  # Random number for each encryption
    a = pow(g, k, p)  # a = g^k mod p
    b = [(ord(char) * pow(y, k, p)) % p for char in plaintext]  # b = M * y^k mod p for each character
    return a, b

def decrypt(private_key, a, b, p):
    x = private_key
    a_inv = mod_inverse(pow(a, x, p), p)  # a^-x mod p
    plaintext = ''.join([chr((char * a_inv) % p) for char in b])
    return plaintext

public_key, private_key = generate_keys()

@audio.route("/encode")
def audio_encode():
    return render_template("encode-audio.html")


@audio.route("/encode-result", methods=['POST', 'GET'])
def audio_encode_result():
    if request.method == 'POST':
        message = request.form['message']
        if 'file' not in request.files:
            flash('No audio found')
        file = request.files['audio']

        if file.filename == '':
            flash('No audio selected')

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(
                current_app.config['UPLOAD_AUDIO_FOLDER'], filename))
            audio_encryption = True
            encrypt_audio(os.path.join(
                current_app.config['UPLOAD_AUDIO_FOLDER'], filename), message)
        else:
            audio_encryption = False
        result = request.form

        message = str(message)

        a, b = encrypt(public_key, message)
        string = f"{a} " + ' '.join(map(str, b))

        return render_template("encode-audio-result.html", result=result, file=file, audio_encryption=audio_encryption, message=message, string = string)


@audio.route("/decode")
def audio_decode():
    return render_template("decode-audio.html")


@audio.route("/decode-result", methods=['POST', 'GET'])
def audio_decode_result():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No audio found')
        file = request.files['audio']
        if file.filename == '':
            flash('No audio selected')
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(
                current_app.config['UPLOAD_AUDIO_FOLDER'], filename))
            audio_decryption = True
            message = decrypt_audio(os.path.join(
                current_app.config['UPLOAD_AUDIO_FOLDER'], filename))
        else:
            audio_decryption = False
        result = request.form
        return render_template("decode-audio-result.html", result=result, file=file, audio_decryption=audio_decryption, message=message)



def encrypt_audio(audio, message):
    song = wave.open(audio, mode='rb')
    # Read frames and convert to byte array
    frame_bytes = bytearray(list(song.readframes(song.getnframes())))

    # The "secret" text message
    plaintext = str(message)

    a, b = encrypt(public_key, plaintext)
    string = f"{a} " + ' '.join(map(str, b))
    print(f"Encrypted text: {string}")


    # Append dummy data to fill out rest of the bytes. Receiver shall detect and remove these characters.
    string = string + int((len(frame_bytes)-(len(string)*8*8))/8) * '#'
    # Convert text to bit array
    bits = list(
        map(int, ''.join([bin(ord(i)).lstrip('0b').rjust(8, '0') for i in string])))

    # Replace LSB of each byte of the audio data by one bit from the text bit array
    for i, bit in enumerate(bits):
        frame_bytes[i] = (frame_bytes[i] & 254) | bit
    # Get the modified bytes
    frame_modified = bytes(frame_bytes)

    # Write bytes to a new wave audio file
    with wave.open(os.path.join(current_app.config['UPLOAD_AUDIO_FOLDER'], "song_embedded.wav"), 'wb') as fd:
        fd.setparams(song.getparams())
        fd.writeframes(frame_modified)
    song.close()


def decrypt_audio(audio):
    song = wave.open(audio, mode='rb')
    # Convert audio to byte array
    frame_bytes = bytearray(list(song.readframes(song.getnframes())))

    # Extract the LSB of each byte
    extracted = [frame_bytes[i] & 1 for i in range(len(frame_bytes))]
    # Convert byte array back to string
    string = "".join(chr(
        int("".join(map(str, extracted[i:i+8])), 2)) for i in range(0, len(extracted), 8))
    # Cut off at the filler characters
    cipher_text = string.split("###")[0]

    cipher_parts = list(map(int, cipher_text.split()))
    
    a = cipher_parts[0]
    b = cipher_parts[1:]
    decoded = decrypt(private_key, a, b, public_key[0])
    print(f"Decrypted text: {decoded}")

    # Print the extracted text
    song.close()
    return decoded
