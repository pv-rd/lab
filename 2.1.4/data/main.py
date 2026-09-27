from data import *

x = Value(10, 1)

name = '0_cool.txt'
Tk = 296

T = Data()
T.read(name, sep = ',')

Y = [Value(log((T.value[i] - Tk)/(T.value[0] - Tk))) for i in range(len(T))]
X = [Value(i) for i in range(len(T))]
x = Data(X)
y = Data(Y)

plot = Plot(x, y, 'Время, с', 'linear T')
plot.draw()

