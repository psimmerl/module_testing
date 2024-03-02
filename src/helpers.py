import numpy as np


################################################################
################################################################
# Extended teminal output (alerts, tables, text formatting, etc)

def alert(msg, c="w", frame=None):
    pass


#################################################################
################################################################
# Math (makes numpy a little lesss chunky sometimes)

# def floor(x, out=None, where=True):
#     return np.floor(x, out=out, where=where)

# def ceil(x, out=None, where=True):
#     return np.ceil(x, out=out, where=where)

# def trunc(x, out=None, where=True):
#     return np.trunc(x, out=out, where=where)

def divide(a, b, out=None, where=True):
    if isinstance(out, (int, float)):
        out = np.full_like(a, out)

    return np.divide(a, b, where=((b!=0)&where), out=out)

# ----
def land(*xs, out=None, where=True):
    x = xs.pop()
    while len(xs):
        x = np.logical_and(x, xs.pop(), out=out, where=where)
    return x

def lor(*xs, out=None, where=True):
    x = xs.pop()
    while len(xs):
        x = np.logical_or(x, xs.pop(), out=out, where=where)
    return x

def lnot(x, out=None, where=True):
    return np.logical_not(x, out=out, where=where)

def lxor(*xs, out=None, where=True):
    x = xs.pop()
    while len(xs):
        x = np.logical_xor(x, xs.pop(), out=out, where=where)
    return x

# ----

################################################################
################################################################
# Plotting stuff

# def fix_yrange(hmin, hmax, zero_floor=False):
#     if zero_floor and hmin - 5*BOT_MARGIN*(hmax-hmin) < 0:
#         hmin, hmax = 0, hmax + TOP_MARGIN*hmax
#     else:
#         mult = (1 + BOT_MARGIN + TOP_MARGIN) * (hmax - hmin)
#         hmin, hmax = hmin - BOT_MARGIN*mult, hmax + TOP_MARGIN*mult
#     return hmin, hmax