from parcs.server import Service, serve
import logging

def repeating_xor_decrypt(ciphertext, key_bytes):
    """Decrypt by XORing the ciphertext with the key repeated."""
    decrypted = bytearray()
    key_len = len(key_bytes)
    for i, b in enumerate(ciphertext):
        decrypted.append(b ^ key_bytes[i % key_len])
    return bytes(decrypted)

class Decryptor(Service):
    def run(self):
        # Receive parameters from the runner:
        #   1. The ciphertext as a hex string.
        #   2. The start key (inclusive) of the keyspace to try.
        #   3. The end key (exclusive).
        #   4. A known plaintext prefix to confirm correct decryption.
        ciphertext_hex = self.recv()
        start_key = self.recv()
        end_key = self.recv()
        known_prefix = self.recv()
        
        logging.info(f"Decryptor: Searching keys in range [{start_key}, {end_key}) for prefix '{known_prefix}'")
        ciphertext = bytes.fromhex(ciphertext_hex)
        found = None

        # Try each candidate key in the given range.
        for key in range(start_key, end_key):
            # Represent the 16-bit key as 2 bytes (big-endian).
            key_bytes = key.to_bytes(2, byteorder='big')
            decrypted = repeating_xor_decrypt(ciphertext, key_bytes)
            try:
                decrypted_text = decrypted.decode('utf-8')
            except UnicodeDecodeError:
                continue  # Skip invalid decodings.
            if decrypted_text.startswith(known_prefix):
                found = (key, decrypted_text)
                logging.info(f"Decryptor: Found key {key} yielding '{decrypted_text}'")
                break

        # Send back the candidate solution (or None if not found).
        self.send(found)

serve(Decryptor())
