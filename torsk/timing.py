from time import time
from torsk.numpy_accelerate import *

class Timer(object):

    def __init__(self,timing_depth=3,flush=True):
        self.depth         = 0
        self.times         = {}        
        self.time_stack    = []
        self.context_stack    = ["/"]
        self.flush = flush
        self.timing_depth  = timing_depth
        
    def begin(self,ctx):
        self.depth += 1
        if(self.depth <= self.timing_depth):
            self.context_stack.append(ctx) # append = push
            if self.flush: bh_flush()
            self.time_stack.append(time())

    def end(self):
        self.depth -= 1
        if(self.depth < self.timing_depth):
            if self.flush: bh_flush()
            path = '/'.join(self.context_stack)            
            t = time() - self.time_stack.pop() 

            if path in self.times.keys():
                self.times[path] += t
            else:
                self.times[path] = t

            self.context_stack.pop()
                
    
    def minus(self,times0):
        time_difference = {}
        for k in self.times.keys():
            if k in times0.keys():
                time_difference[k] = self.times[k] - times0[k]
            else:
                time_difference[k] = self.times[k]

        return time_difference

    def reset(self):
        self.times = {}
    
    def pretty_print(self):
        s = "Accumulated timing:\n"
        keys_r = list(self.times.keys()); keys_r.reverse()
        for k in keys_r:
            prefix    = k.rfind("/")+1
            pretty_k  = (' '*prefix) + k[prefix:]
            s += "%s:\t%.3fs\n" % (pretty_k,self.times[k])
        return s


def start_timer(timer,context):
    if timer is not None:
        timer.begin(context)

def end_timer(timer):
    if timer is not None:
        timer.end()
