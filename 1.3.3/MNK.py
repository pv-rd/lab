from Data import *

def MNK(X: Data, Y: Data):
    x = X.v
    y = Y.v
    xy = x * y
    xx = x * x
    yy = y * y
    _x = x.mean()
    _y = y.mean()
    _xx = xx.mean()
    _yy = yy.mean()
    _xy = xy.mean()

    k = (_xy - _x*_y) / (_xx - _x*_x)
    b = _y - k * _x

    ks = ((((_yy - _y*_y) / (_xx - _x*_x)) - k**2) / len(x))**0.5
    bs = ks * (_xx - _x*_x)**0.5

    return (Value(k, ks), Value(b, bs))

