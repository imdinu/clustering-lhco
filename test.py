import tqdm
from time import sleep
import multiprocessing as mpi
import numpy as np
from collections import deque

mpi.set_start_method('fork')
n_procs = 4
pbars = [tqdm.tqdm(total=100, position=i+1, leave=0, ncols=79, bar_format='{l_bar}{bar}')
         for i in range(n_procs)]


def do_stuff(bars, start, stop):
    pno = mpi.current_process()._identity[0]
    bar = bars[(pno-1) % len(bars)]
    for _ in range(start, stop):

        sleep(0.1-0.005*pno)
        bar.desc = f"Process{pno}"
        bar.update(1)

    return 0


procs = [mpi.Process(target=do_stuff,
                     args=(pbars, 0, 100))
         for i
         in range(16)]
q = deque(procs)
p = mpi.Queue(n_procs)

main_bar = tqdm.tqdm(total=len(procs), desc="Processed Chunks", ncols=79,
                     position=0, bar_format='{l_bar}{bar}{elapsed}', colour="green")

finished = np.zeros(n_procs).astype(bool)
while sum(finished) < len(procs):
    working = np.sum(list(map(lambda obj: obj.is_alive(), procs)))
    if working >= n_procs:
        sleep(0.1)
    else:
        exited = np.array(
            list(map(lambda obj: obj.exitcode, procs))) != None
        done = np.sum(exited) - np.sum(finished)
        main_bar.update(done)
        finished = exited
        if len(q) > 0:
            q.popleft().start()
