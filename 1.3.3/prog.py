from Plot import *
file = "D:/Labs/1.3.3/1.txt"
X = Data()
Y = Data()
X.read(file, 0, e = 1)
Y.read(file, 1, e = 0.001, sep_dec = ',')

p = Plot(X, Y, "$\Delta P$, ед.", "Q, л/мин")
p.draw(0,18, legend = False)

