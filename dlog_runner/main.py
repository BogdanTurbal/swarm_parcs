import os
import math
import logging
from parcs.server import Runner, serve

def split_range(total, partitions):
    chunk = math.ceil(total / partitions)
    ranges = []
    start = 0
    while start < total:
        end = min(start + chunk, total)
        ranges.append((start, end))
        start = end
    return ranges

class DlogRunner(Runner):
    def run(self):
        # Read parameters from environment variables:
        # P_PRIME: the prime p
        # G: the generator g
        # H: the target h
        # P: number of worker partitions
        p = int(os.environ.get('P_PRIME', '101'))
        g = int(os.environ.get('G', '2'))
        h = int(os.environ.get('H', '1'))
        partitions = int(os.environ.get('P', '4'))
        
        logging.info(f"Runner: Solving discrete log for p={p}, g={g}, h={h} using {partitions} workers")
        
        ranges = split_range(p, partitions)
        tasks = []
        solution = None
        
        # Launch a DlogSolver service for each range.
        for (start, end) in ranges:
            task = self.engine.run('bogdanturbal/dlog-solver-py')
            task.send_all(p, g, h, start, end)
            tasks.append(task)
        
        # Collect results from tasks.
        for task in tasks:
            result = task.recv()
            if result is not None:
                solution = result
                logging.info(f"Runner: Found solution x = {result}")
                break
        
        for task in tasks:
            task.shutdown()
        
        if solution is not None:
            logging.info(f"Discrete Log Successful: x = {solution}")
        else:
            logging.info("Discrete Log: No solution found.")
            
serve(DlogRunner())
