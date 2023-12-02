import numpy as np


################################################################
################################################################


# Extended teminal output (alerts, tables, text formatting, etc)
def alert(msg, c="w", frame=None):
    pass


#################################################################
################################################################


# Math
def divide(a, b, out=0):
    if isinstance(out, np.ndarray):
        out = np.divide(a, b, where=b != 0, out=out)
    else:
        out = np.divide(a, b, where=b != 0, out=np.full_like(a, out))
    return out


################################################################
################################################################

#
