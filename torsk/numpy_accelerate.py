import numpy as np
from torsk.config import *

Id = lambda A: A
def void():
    return

if numpy_acceleration == "bohrium":
    import bohrium 

    bh = bohrium
    bh_type  = bh.ndarray
    bh_check = bh.bhary.check    
    to_bh    = bh.array
    to_np_base = bh.array #bh.interop_numpy.get_array
    bh_flush = bh.flush
    
    def to_np(A):
        if bh_check(A):
            return A.copy2numpy()
        #return bh.interop_numpy.get_array(A)
        else:
            return A
    
elif numpy_acceleration == "bh107":
    import bh107

    bh       = bh107
    bh_type  = bh.BhArray
    bh_check = lambda A: isinstance(A,bh.BhArray)    
    to_bh    = bh.BhArray.from_numpy
    to_np_base = lambda A: A.asnumpy();
    bh_flush = bh.flush
    
    def to_np(A):
        if isinstance(A,bh_type):
            return A.asnumpy()
        else:
            return A


else:
    bh = np
    bh_type  = bh.ndarray
    bh_check = lambda A: isinstance(A,bh_type);
    to_bh      = Id
    to_np      = Id
    to_np_base = Id
    bh_flush   = void


    
def before_storage(model):
    numpyize(model)

def after_storage(model,old_state=None):
    bohriumize(model,old_state)        

def bohriumize(model,old_state=None):
    print("Bohriumizing...")
    if old_state is None:
        model.esn_cell.weight_hh.values = bh.array(model.esn_cell.weight_hh.values.astype(np.float64))
        model.esn_cell.weight_hh.col_idx = bh.array(model.esn_cell.weight_hh.col_idx.astype(np.int32))
        model.ones = bh.array(model.ones.astype(np.float64))
        model.wout = bh.array(model.wout.astype(np.float64))
    else:
        model.esn_cell.weight_hh.values  = old_state["esn_cell.weight_hh.values"]
        model.esn_cell.weight_hh.col_idx = old_state["esn_cell.weight_hh.col_idx"]
        model.ones = old_state["ones"] 
        model.wout = old_state["wout"]
    print("Done bohriumizing...")

def numpyize(model):
    print("Numpyizing...")
    old_state = {};
    old_state["esn_cell.weight_hh.values"]  = model.esn_cell.weight_hh.values;
    old_state["esn_cell.weight_hh.col_idx"] = model.esn_cell.weight_hh.col_idx;
    old_state["ones"] = model.ones; 
    old_state["wout"] = model.wout;
    
    model.esn_cell.weight_hh.values  = to_np(model.esn_cell.weight_hh.values)
    model.esn_cell.weight_hh.col_idx = to_np(model.esn_cell.weight_hh.col_idx)
    model.ones = to_np(model.ones)
    model.wout = to_np(model.wout)
    
    #E = {}
    for D in [model.__dict__, model.esn_cell.__dict__, model.esn_cell.weight_hh.__dict__]:
        for k,v in D.items():
            if isinstance(v,bh_type):
                print("Numpyizing ",k)
                #E[k] = v
                D[k] = to_np(v)                        
    #return E

    return old_state