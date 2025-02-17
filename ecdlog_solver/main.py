from parcs.server import Service, serve
import logging

# --- Elliptic Curve Arithmetic Utilities ---

def mod_inv(a, p):
    # Compute modular inverse using Fermat's little theorem (p is prime)
    return pow(a, p - 2, p)

def point_add(P, Q, a, p):
    if P is None:
        return Q
    if Q is None:
        return P
    # Check for inverse points
    if P[0] == Q[0] and (P[1] + Q[1]) % p == 0:
        return None
    if P != Q:
        # Slope: (y2 - y1)/(x2 - x1)
        s = ((Q[1] - P[1]) * mod_inv(Q[0] - P[0], p)) % p
    else:
        # Doubling: s = (3*x1^2 + a)/(2*y1)
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

# --- ECDLP Solver Service ---

class ECDLPSolver(Service):
    def run(self):
        # Receive parameters (all integers):
        # p: prime modulus
        # a, b: curve coefficients for y^2 = x^3 + a*x + b (mod p)
        # P_x, P_y: generator point coordinates (P)
        # Q_x, Q_y: target point coordinates (Q = k * P)
        # start, end: search interval for k
        p      = self.recv()
        a      = self.recv()
        b      = self.recv()  # not used in computation but provided for completeness
        P_x    = self.recv()
        P_y    = self.recv()
        Q_x    = self.recv()
        Q_y    = self.recv()
        start  = self.recv()
        end    = self.recv()

        logging.info(f"ECDLP Solver: Searching for k in range [{start}, {end})")
        P = (P_x, P_y)
        Q = (Q_x, Q_y)
        solution = None
        for k in range(start, end):
            R = scalar_mult(k, P, a, p)
            if R == Q:
                solution = k
                logging.info(f"ECDLP Solver: Found solution k = {k}")
                break
        self.send(solution)

serve(ECDLPSolver())
