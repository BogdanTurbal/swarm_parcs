from parcs.server import Service, serve
import logging

class DlogSolver(Service):
    def run(self):
        # Receive parameters: p, g, h, start, end.
        p = self.recv()
        g = self.recv()
        h = self.recv()
        start = self.recv()
        end = self.recv()
        logging.info(f"Solver: Searching x in range [{start}, {end}) for which {g}^x mod {p} == {h}")
        solution = None
        for x in range(start, end):
            if pow(g, x, p) == h:
                solution = x
                logging.info(f"Solver: Found solution x = {x}")
                break
        self.send(solution)

serve(DlogSolver())
