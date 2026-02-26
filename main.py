import os
import random

import math
from hashlib import sha256
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from NtruEncrypt import decrypt, encrypt, generate_keypair
from num_to_polynomial import koblitz_decoder, koblitz_encoder, points_decoder

DNA_ENCODING = {
    '00': 'A',
    '01': 'T',
    '10': 'C',
    '11': 'G',
}
DNA_DECODING = {v: k for k, v in DNA_ENCODING.items()}


def logistic_map(x0, r, iterations):
    """Return x_n of logistic map after n iterations."""
    x = x0
    for _ in range(iterations):
        x = r * x * (1 - x)
    return x


def generate_logistic_sequence(x0, r, length):
    """Generate x_i for i in [0, length), where x_0 = x0."""
    if length <= 0:
        return []

    sequence = [x0]
    x = x0
    for _ in range(1, length):
        x = r * x * (1 - x)
        sequence.append(x)
    return sequence


def dna_confuse(data, x0, r):
    """DNA confusion with chaotic permutation."""
    binary = ''.join(format(byte, '08b') for byte in data)

    dna_sequence = [DNA_ENCODING[binary[i:i + 2]] for i in range(0, len(binary), 2)]

    chaotic = generate_logistic_sequence(x0, r, len(dna_sequence))
    indices = sorted(range(len(dna_sequence)), key=lambda i: chaotic[i])
    confused_dna = [dna_sequence[i] for i in indices]

    confused_binary = ''.join(DNA_DECODING[base] for base in confused_dna)
    return bytes(int(confused_binary[i:i + 8], 2) for i in range(0, len(confused_binary), 8))


def dna_deconfuse(data, x0, r):
    """Reverse DNA confusion."""
    binary = ''.join(format(byte, '08b') for byte in data)

    dna_sequence = [DNA_ENCODING[binary[i:i + 2]] for i in range(0, len(binary), 2)]

    chaotic = generate_logistic_sequence(x0, r, len(dna_sequence))
    indices = sorted(range(len(dna_sequence)), key=lambda i: chaotic[i])
    inverse_indices = [0] * len(indices)
    for pos, idx in enumerate(indices):
        inverse_indices[idx] = pos

    original_dna = [dna_sequence[i] for i in inverse_indices]
    original_binary = ''.join(DNA_DECODING[base] for base in original_dna)
    return bytes(int(original_binary[i:i + 8], 2) for i in range(0, len(original_binary), 8))


def generate_chaos_params(key):
    hash_value = sha256(key).digest()

    x0 = (int.from_bytes(hash_value[:4], byteorder='big') / 0xFFFFFFFF) % 1
    x0 = max(0.1, min(0.9, x0))

    r = (int.from_bytes(hash_value[4:8], byteorder='big') / 0xFFFFFFFF) * 0.3 + 3.7
    return x0, r


def generate_chaos_sbox(key):
    a = 1.4
    b = 0.3
    x = sum(key) / 256
    y = sum(key[::-1]) / 256

    chaos_sequence = []
    for _ in range(256):
        chaos_sequence.append(int((x + y) * 128) & 0xFF)
        x_new = 1 - a * x * x + y
        y_new = b * x
        x = math.tanh(x_new)
        y = math.tanh(y_new)

    # Convert chaotic values into a deterministic permutation (bijective S-box).
    ranked = sorted(range(256), key=lambda i: (chaos_sequence[i], i))
    sbox = [0] * 256
    for out_value, in_index in enumerate(ranked):
        sbox[in_index] = out_value
    return sbox


class SM4:
    def __init__(self, key, sbox):
        self.key = key
        self.sbox = sbox
        self.backend = default_backend()
        self.inv_sbox = [0] * 256
        for i, value in enumerate(sbox):
            self.inv_sbox[value] = i

    def encrypt(self, data):
        iv = os.urandom(16)
        cipher = Cipher(algorithms.SM4(self.key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()

        transformed = bytes(self.sbox[byte] for byte in padded_data)
        ct = encryptor.update(transformed) + encryptor.finalize()
        return iv + ct

    def decrypt(self, data):
        iv = data[:16]
        ct = data[16:]
        cipher = Cipher(algorithms.SM4(self.key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(ct) + decryptor.finalize()

        decrypted_bytes = bytes(self.inv_sbox[byte] for byte in decrypted_padded)
        unpadder = padding.PKCS7(128).unpadder()
        try:
            return unpadder.update(decrypted_bytes) + unpadder.finalize()
        except ValueError:
            print('Invalid padding bytes. Decryption failed.')
            return decrypted_bytes


def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0:
        return False

    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def generate_random_prime(min_range=2, max_range=100):
    while True:
        num = random.randint(min_range, max_range)
        if is_prime(num):
            return num


if __name__ == '__main__':
    d = 7
    p = 5
    q = 1024

    print('==========Alice加密流程===========\n')

    sm4_key_hex = '12345678900987654321123456789014'
    sm4_key = bytes.fromhex(sm4_key_hex)

    elliptic_a = generate_random_prime()
    elliptic_b = generate_random_prime()
    while elliptic_a == elliptic_b:
        elliptic_b = generate_random_prime()

    print(f'原始SM4密钥(hex): {sm4_key_hex}')

    character_polynomials, n = koblitz_encoder(sm4_key_hex, elliptic_a, elliptic_b)
    print(f'\nSM4密钥转换为多项式完成，多项式数量：{len(character_polynomials)}')

    public_key, private_key = generate_keypair(p, q, d, n)
    print('\nNTRU公钥生成完成：')
    print(public_key.print_polynomial())

    print('\nSM4密钥加密过程：')
    cipher_polys = []
    for element in character_polynomials:
        cipher_polys.append(encrypt(element, public_key, d, n, q))

    user_message = input('\n请输入明文(直接回车使用默认值 helloworldfromwx): ').strip()
    if not user_message:
        user_message = 'helloworldfromwx'
    message = user_message.encode('utf-8')
    print(f'\n原始明文：{message.decode()}')

    x0, r = generate_chaos_params(sm4_key)
    print(f'\n混沌参数生成完成，x0={x0:.6f}，r={r:.6f}')

    confused_msg = dna_confuse(message, x0, r)
    print('\nDNA混淆完成，混淆后消息：')
    print(confused_msg.hex())

    sbox = generate_chaos_sbox(sm4_key)
    print('\n混沌S盒生成完成')

    sm4 = SM4(sm4_key, sbox)
    ct = sm4.encrypt(confused_msg)
    print('\nSM4加密完成，密文：')
    print(ct.hex())

    print('\n==========Bob解密流程===========\n')

    print('SM4密钥解密过程：')
    dec_w = []
    for element in cipher_polys:
        decrypted_message = decrypt(element, private_key, p, q, n)
        dec_w.append(decrypted_message.coeffs)

    decrypted_sm4_key = koblitz_decoder(points_decoder(dec_w))
    decrypted_sm4_key_bytes = bytes.fromhex(decrypted_sm4_key)
    print('解密后的SM4密钥：')
    print(decrypted_sm4_key_bytes.hex())

    sbox_decrypted = generate_chaos_sbox(decrypted_sm4_key_bytes)
    print('\n混沌S盒生成完成')

    sm4_decrypted = SM4(decrypted_sm4_key_bytes, sbox_decrypted)
    decrypted_data = sm4_decrypted.decrypt(ct)
    print('\nSM4解密完成，解密后消息：')
    print(decrypted_data.hex())

    x0_decrypted, r_decrypted = generate_chaos_params(decrypted_sm4_key_bytes)
    print(f'\n混沌参数生成完成，x0={x0_decrypted:.6f}，r={r_decrypted:.6f}')

    deconfused_data = dna_deconfuse(decrypted_data, x0_decrypted, r_decrypted)
    print('\nDNA解混淆完成，解密后消息：')
    try:
        print(deconfused_data.decode('utf-8'))
    except UnicodeDecodeError:
        print('Decryption error! Result bytes:', deconfused_data.hex())

