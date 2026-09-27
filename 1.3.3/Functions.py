from math import *
import numpy as np
import warnings as w 
from Value import * 
F = {
    'sin': (
        lambda x: np.sin(x),
        lambda x: np.cos(x)
    ),
    'cos': (
        lambda x: np.cos(x),
        lambda x: -np.sin(x),
    ),
    'tan': (
        lambda x: np.tan(x),
        lambda x: 1/(np.cos(x)**2),
    ),
    'exp': (
        lambda x: np.exp(x),
        lambda x: np.exp(x),
    ),
    'log': (
        lambda x: np.log(x),
        lambda x: 1/x,
    ),
    'sqrt': (
        lambda x: np.sqrt(x),
        lambda x: 0.5/np.sqrt(x)
    )
}

G = {
    '__pow__': (
        lambda x, y: x ** y,
        lambda x, y: y * (x ** (y-1)),
        lambda x, y: np.log(x) * (x ** y),
    ),
    '__rpow__': (
        lambda y, x: x ** y,
        lambda y, x: y * (x ** (y-1)),
        lambda y, x: np.log(x) * (x ** y),
    )
}

def F_add(cls):
    for f in F.keys():
        def make_method(f):
            def method(self):
                v = self.v
                if any(v == 0): w.warn("It has zero(es)", UserWarning)
                V = F[f][0](self.v)
                E = np.abs(F[f][1](self.v))*self.e
                return cls(V, E)
            return method
        setattr(cls, f, make_method(f))
    return cls

def G_add(cls):
    for g in G.keys():
        def make_method(g):
            def method(self, other):
                if isinstance(other, (int, float)):
                    other = Value(other)
                elif not isinstance(other, (Value, cls)):
                    return NotImplemented
                x = self.v
                y = other.v
                ex = self.e
                ey = other.e
                if any(x == 0) or any(y == 0): w.warn("They have zero(es)", UserWarning)

                V = G[g][0](x, y)

                derx = G[g][1](x, y)
                dery = G[g][2](x, y)

                E = ((derx * ex)**2 + (dery * ey)**2)**0.5

                return cls(V, E)
            return method
        setattr(cls, g, make_method(g))
    return cls
