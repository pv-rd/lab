from math import log
class Plot():
    
    def __init__(self, x, ex = 0, y=0, ey = 0, x_title = "x, ед.", y_title = "y, ед.", scale = '1:1'):
        self.x = x
        self.y = y
        self.ex = ex
        self.ey = ey
        A = scale.split(':')
        self.mx = float(A[0])
        self.my = float(A[1])
        self.x_title = x_title
        self.y_title = y_title

    def draw(self, font_size = 16, fig_size = (7,7), point = '.m', color = 'c', legend = False, file = 'plot.png', show = True):
        import numpy as np
        import matplotlib.pyplot as plt
        import matplotlib as mpl

        mpl.rcParams['font.size'] = font_size
        plt.figure(figsize= fig_size)


        plt.ylabel(self.y_title)
        plt.xlabel(self.x_title)

        plt.errorbar(self.x, self.y, yerr=self.ey, xerr=self.ex, fmt= point)

        plt.grid(True)

        K, B = MNK(self.x, self.y)
        k = K[0]
        b = B[0]

        x = np.linspace(min(self.x)*0.90, max(self.x)*1.05, 100)
        y = k*x + b
        plt.plot(x, y, color)

        if legend: plt.legend()
        plt.savefig(file)
        if show: plt.show()

    def approx(self):
        return MNK(self.x, self.y)




def mean(X):
    S = sum(X)
    N = len(X)
    return S/N

def MNK(X, Y):
    x = X
    y = Y
    xy = [x[i] * y[i] for i in range(len(x))]
    xx = [x[i] * x[i] for i in range(len(x))]
    yy = [y[i] * y[i] for i in range(len(y))]
    _x = mean(x)
    _y = mean(y)
    _xx = mean(xx)
    _yy = mean(yy)
    _xy = mean(xy)

    k = (_xy - _x*_y) / (_xx - _x*_x)
    b = _y - k * _x

    ks = ((((_yy - _y*_y) / (_xx - _x*_x)) - k**2) / len(x))**0.5
    bs = ks * (_xx - _x*_x)**0.5

    return ((k, ks), (b, bs))
    
def read(file_name):
    with open(file_name, 'r') as file:
        A = [float(line.replace(',', '.')) for line in file]
        return A

Y = read('0.txt')
X = [i for i in range(len(Y))]


Y = [x/760*101325 * 0.00001 for x in Y]

p = Plot(x=X, y=Y, x_title = "t, c", y_title = "P, Па")
p.draw()
print(p.approx())