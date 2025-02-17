import os
import math
import logging
from parcs.server import Runner, serve

def split_range(total, partitions):
    """Split the keyspace [0, total) into roughly equal ranges."""
    chunk = math.ceil(total / partitions)
    ranges = []
    start = 0
    while start < total:
        end = min(start + chunk, total)
        ranges.append((start, end))
        start = end
    return ranges

class DecryptorRunner(Runner):
    def run(self):
        # Read parameters from environment:
        # CIPHERTEXT: The encrypted message as a hex string.
        # PREFIX: The known plaintext prefix.
        # MAX_KEY: Upper bound of keyspace (default 65536 for a 16-bit key).
        # P: Number of partitions (parallel tasks to launch).
        ciphertext_hex = os.environ.get('CIPHERTEXT')
        known_prefix = os.environ.get('PREFIX', '')
        max_key = int(os.environ.get('MAX_KEY', 65536))
        partitions = int(os.environ.get('P', 4))
        
        logging.info(f"Runner: Starting decryption with MAX_KEY={max_key}, partitions={partitions}, prefix='{known_prefix}'")
        key_ranges = split_range(max_key, partitions)
        tasks = []
        solution = None

        # Launch a decryption service for each key range.
        for (start, end) in key_ranges:
            task = self.engine.run('bogdanturbal/decryptor-py')
            task.send_all(ciphertext_hex, start, end, known_prefix)
            tasks.append(task)
        
        # Collect results from tasks.
        for task in tasks:
            result = task.recv()
            if result is not None:
                solution = result
                logging.info(f"Runner: Found solution: key={result[0]}, decrypted='{result[1]}'")
                # Optionally, stop early if one valid result is sufficient.
                break

        # Shut down all tasks.
        for task in tasks:
            task.shutdown()
        
        if solution:
            logging.info(f"Runner: Decryption successful: key={solution[0]}, message='{solution[1]}'")
        else:
            logging.info("Runner: No valid key found in the given keyspace.")

serve(DecryptorRunner())
