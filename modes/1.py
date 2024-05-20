import random
from sympy import mod_inverse

def generate_keys():
    # Using a large prime number for the modulus
    p = 104729  # A prime number
    g = 2  # Primitive root modulo of p

    # Private key
    x = random.randint(1, p-2)  # Private key x

    # Public key
    y = pow(g, x, p)  # y = g^x mod p

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

# Main function to handle user input and encryption/decryption
def main():
    public_key, private_key = generate_keys()

    # Encrypt
    plaintext = input("Enter the text to encrypt: ")
    a, b = encrypt(public_key, plaintext)
    cipher_text = f"{a} " + ' '.join(map(str, b))
    print(f"Encrypted text: {cipher_text}")

    # Decrypt
    cipher_text = input("Enter the cipher text to decrypt: ")
    cipher_parts = list(map(int, cipher_text.split()))
    a = cipher_parts[0]
    b = cipher_parts[1:]
    decrypted_text = decrypt(private_key, a, b, public_key[0])
    print(f"Decrypted text: {decrypted_text}")

if __name__ == "__main__":
    main()
