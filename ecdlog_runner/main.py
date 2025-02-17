import os
import math
import logging
from parcs.server import Runner, serve

# --- Replicate EC Arithmetic for Q computation in the runner ---

def mod_inv(a, p):
    return pow(a, p-2, p)

def point_add(P, Q, a, p):
    if P is None:
        return Q
    if Q is None:
        return P
    if P[0] == Q[0] and (P[1] + Q[1]) % p == 0:
        return None
    if P != Q:
        s = ((Q[1] - P[1]) * mod_inv(Q[0] - P[0], p)) % p
    else:
        s = ((3 * P[0] * P[0] + a) * mod_inv(2 * P[1], p)) % p
    x_r = (s * s - P[0] - Q[0]) % p
    y_r = (s * (P[0] - x_r) - P[1]) % p
    return (x_r, y_r)

def scalar_mult(k, P, a, p):
    result = None
    addend = P
    while k:
        if k & 1:
            result = point_add(result, addend, a, p)
        addend = point_add(addend, addend, a, p)
        k //= 2
    return result

# --- ECDLP Runner ---

class ECDLPRunner(Runner):
    def run(self):
        # Read fixed curve parameters from environment:
        # p: prime modulus, CURVE_A, CURVE_B for the curve equation.
        p = int(os.environ.get('P_PRIME', '751'))
        a = int(os.environ.get('CURVE_A', '1'))
        b = int(os.environ.get('CURVE_B', '1'))
        P_x = int(os.environ.get('P_X', '0'))
        P_y = int(os.environ.get('P_Y', '1'))
        # SEARCH_SPACE defines the total range in which we look for k.
        search_space = int(os.environ.get('SEARCH_SPACE', str(p)))
        # SECRET_K is the actual secret used to generate Q.
        secret_k = int(os.environ.get('SECRET_K', '5'))
        workers = int(os.environ.get('WORKERS', '1'))
        
        # Compute Q = secret_k * P:
        P_point = (P_x, P_y)
        Q_point = scalar_mult(secret_k, P_point, a, p)
        Q_x, Q_y = Q_point
        
        logging.info(f"Runner: Using secret k = {secret_k} to compute Q = {Q_point}")
        logging.info(f"Runner: Searching over [0, {search_space}) with {workers} worker(s)")
        
        # Split the search range [0, search_space) among workers:
        def split_range(total, partitions):
            chunk = math.ceil(total / partitions)
            ranges = []
            start = 0
            while start < total:
                end = min(start + chunk, total)
                ranges.append((start, end))
                start = end
            return ranges
        
        ranges = split_range(search_space, workers)
        tasks = []
        solution = None
        
        # Launch tasks for each sub-range.
        for r in ranges:
            task = self.engine.run('myusername/ecdlog-solver-py')
            task.send_all(p, a, b, P_x, P_y, Q_x, Q_y, r[0], r[1])
            tasks.append(task)
        
        # Collect results.
        for task in tasks:
            res = task.recv()
            if res is not None:
                solution = res
                logging.info(f"Runner: Found solution k = {solution}")
                break
        
        for task in tasks:
            task.shutdown()
        
        if solution is not None:
            logging.info(f"ECDLP successful: k = {solution}")
        else:
            logging.info("ECDLP: No solution found in the given search space.")
            
serve(ECDLPRunner())
