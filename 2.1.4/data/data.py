from math import *

class Value():
    def __init__(self, value = 0.0, error = 0.0):
        self.value = value
        self.error = abs(error)
        if self.value == 0:
            self.relative = inf
        else:
            self.relative = self.error / self.value

        self.length = 2*error
        self.digit()
        self.r = self.value + self.error
        self.l = self.value - self.error

    def read(self, s: str):
        A = s.split()
        B = list()
        for x in A:
            is_number = True
            for c in x:
                if c not in '1234567890.': 
                    is_number = False
                    break
            if is_number:
                B.append(float(x))

        self.value = B[0]
        if len(B) > 1:
            self.error = abs(B[1])
            if self.value == 0:
                self.relative = inf
            else:
                self.relative = self.error / self.value
            self.length = 2*self.error
        self.digit()
        self.r = self.value + self.error
        self.l = self.value - self.error
    
    def digit(self):
        if self.error != 0.0:
            s = str(self.error)
            counter = 0
            if type(self.error) == type(1.1):
                point = s.find('.')
                for c in s:
                    if c != '0' and c != '.': break
                    counter += 1
                if c =='1': counter += 1
                if counter <= point:
                    self.error = round(self.error)
                    self.value = round(self.value)
                    self.right = 0
                    idx = -1
                    
                if counter > point:
                    bound = counter - point
                    self.error = round(self.error, bound)
                    self.value = round(self.value, bound)
                    self.right = bound

            else:
                if self.value != 0:
                    idx = len(s) - 1 
                    while s[idx] == '0': 
                        counter += 1
                        idx = idx - 1
                    if s[idx] == '1' and counter > 0: counter-=1
                    self.value = self.value // 10**counter * 10**counter
                    self.error = self.error // 10**counter * 10**counter
                self.right = 0
        else: 
            s = str(self.value)
            if type(self.value) == type(1.1):
                point = s.find('.')
                self.right = len(s) - point - 1
            else: self.right = 0

    def __add__(self, other):
        if type(other) != type (self):
            return Value(self.value + other, self.error)
        error = (self.error**2 + other.error**2)**0.5
        return Value(self.value + other.value, error)
    
    def __sub__(self, other):
        if type(other) != type (self):
            return Value(self.value - other, self.error)
        error = (self.error**2 + other.error**2)**0.5
        return Value(self.value - other.value, error)
    
    def __mul__(self, other):
        if type(other) != type (self):
            rel = self.relative
            val = self.value * other
        else:
            rel = (self.relative**2 + other.relative**2)**0.5
            val = self.value * other.value
        return Value (val, val * rel)
    
    def __truediv__(self, other):
        if type(other) != type (self):
            rel = self.relative
            val = self.value / other
        else:
            rel = (self.relative**2 + other.relative**2)**0.5
            val = self.value / other.value
        return Value (val, val * rel)

    def __pow__(self, number):
        rel = self.relative * abs(number)
        val = self.value ** number
        return Value (val, val * rel)    

    def __eq__(self, other):
        delta = abs(self.value - other.value)
        if self.error + other.error >= delta: return True
        return False

    def __str__(self):
        return f"{self.value:.{self.right}f} ± {self.error:.{self.right}f}"
    
    def __getitem__(self, key):
        if key == 'value': return(self.value)
     

class Data():

    def __init__(self, A = list()):
        self.data = A[:]
        self.value = [x.value for x in self.data]
        self.error = [x.error for x in self.data]
        if len(self) > 0: self.Average()

    def add(self, value: Value):
        self.data.append(value)
        self.value.append(value.value)
        self.error.append(value.error)
        self.Average()

    def __len__(self):
        return len(self.data)

    def Sum(self):
        S = 0
        for x in self.data:
            S = S + x.value
        self._sum = S
        return S
        
    def Average(self):
        self.s = (self.Sum()/len(self))
        
        S = 0
        for x in self.data:
            S = S + (x.value - self.s)**2
        S = S/len(self)
        self.dispersion = S
        S = S**0.5
        self.dev = S
        self.ae = self.dev/(len(self)**0.5)
        return self.s
    
    def deviation(self):
        self.Average()
        return self.dev
    
    def read(self, file_name, data_type = 'float', sep = '.', column = 0, error_column = -1, error = 0, sep_col = None):
        file = open(file_name, 'r')
        for line in file:
            row = line.split(sep_col)
            for i in range(len(row)):
                if sep != '.':
                    for c in sep:
                        row[i] = row[i].replace(c, '.')
                if data_type == 'float': row[i] = float(row[i])
                elif data_type == 'int': row[i] = int(row[i])
        
            if error_column != -1:
                error = row[error_column]
            
            new_value = Value(row[column], error)

            self.add(new_value)
        file.close()

    def __getitem__(self, key):
        return self.data[key]
    
    def __iter__(self):
        return iter(self.data)
    
    def __add__(self, other):
        R = Data()
        if type(other) != type(Data()):
            for i in range(len(self)): R.add(self[i] + other)
            return R
        if type(other) == type(Data()):
            for i in range(len(self)): R.add(self[i] + other[i])
        return NotImplemented
    
    def __sub__(self, other):
        R = Data()
        if type(other) != type(Data()):
            for i in range(len(self)): R.add(self[i] - other)
            return R
        if type(other) == type(Data()):
            for i in range(len(self)): R.add(self[i] - other[i])
        return NotImplemented

    def __radd___(self, other):
        return self.__add__(other)

    
    def __mul__(self, other):
        R = Data()
        if type(other) != type(Data()):
            for i in range(len(self)): R.add(self[i] * other)
            return R
        for i in range(len(self)): R.add(self[i] * other[i])
        return R
    
    def __truediv__(self, other):
        R = Data()
        if type(other) != type(Data()):
            for i in range(len(self)): R.add(self[i] / other)
            return R
        for i in range(len(self)): R.add(self[i] / other[i])
        return R

    @staticmethod
    def MNK(x : Value, y : Value): # y = kx + b
        k = ((x*y).s - x.s * y.s) / ((x*x).s - (x.s)**2)
        b = y.s - k * x.s

        ks = (((((y*y).s - y.s*y.s) / ((x*x).s - x.s*x.s)) - k**2) / len(x))**0.5
        bs = ks * ((x*x).s - x.s*x.s)**0.5

        return (Value(k, ks), Value(b, bs))
            

class Plot():
    
    def __init__(self, x : Data, y : Data, x_title = 'x, ед.', y_title = 'y, ед.', scale = '1:1'):
        self.X = x
        self.Y = y
        self.x = x.value
        self.y = y.value
        self.ex = x.error
        self.ey = y.error
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

        K, B = Data.MNK(self.X, self.Y)
        k = K.value
        b = B.value

        #x = np.linspace(min(self.x)*0.90, max(self.x)*1.05, 100)
        #y = k*x + b
        plt.plot(x, y, color)

        if legend: plt.legend()
        plt.savefig(file)
        if show: plt.show()