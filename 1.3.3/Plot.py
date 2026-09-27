from Data import *        
from MNK import *   
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
class Plot():
    
    def __init__(self, x : Data, y : Data, x_title = 'x, ед.', y_title = 'y, ед.', scale = '1:1', label = 'График y(x)'):
        self.X = x
        self.Y = y
        self.x = x.v
        self.y = y.v
        self.ex = x.e
        self.ey = y.e

        A = scale.split(':')
        self.mx = float(A[0])
        self.my = float(A[1])

        self.x_title = x_title
        self.y_title = y_title

    def draw(self, 
             start = 0,
             stop = None,
             font_size = 16, 
             fig_size = (7,7), 
             point = '.m', 
             color = 'c', 
             legend = True, 
             file = 'plot.png',
             grid = True, 
             show = True,
             mnk = True):
        
        if stop == None: stop = len(self.X)



        mpl.rcParams['font.size'] = font_size
        plt.figure(figsize=fig_size)



        plt.ylabel(self.y_title)
        plt.xlabel(self.x_title)

        main_label = 'график'
        plt.errorbar(self.x[start:stop], self.y[start:stop], yerr=self.ey[start:stop], xerr=self.ex[start:stop], fmt=point, label=main_label)

        if grid: plt.grid(True)

        if mnk:

            K, B = MNK(Data(self.x[start:stop], self.ex[start:stop]), Data(self.y[start:stop], self.ey[start:stop]))
            k = K.v
            b = B.v

            x = np.linspace(min(self.x[start:stop])*0.90, max(self.x[start:stop])*1.05, 100)
            y = k*x + b
            plt.plot(x, y, color)

        if legend: plt.legend()

        plt.savefig(file)

        if show: plt.show()

