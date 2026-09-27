from math import *

class Value():
    def __init__(self, value = 0.0, error = 0.0):
        self.v = value
        self.e = error
        self._update()

    @property
    def v(self):
        return self._v
    
    @v.setter
    def v(self, value):
        self._v = value
        if hasattr(self, '_e'):
            self._update()

    @property
    def e(self):
        return self._e
    
    @e.setter
    def e(self, error):
        self._e = error
        self._update()


    def __str__(self):
        v, e = self.truncate()
        r = Value.rounder(e)
        if r > 0:
            return f"{v:.{r}f} ± {e:.{r}f}"
        return f"{int(v)} ± {int(e)}"
    
    def __repr__(self):
        return f"Value({self.v}, {self.e})"

    
    # относительная погрешность (relative error)

    def _rel(self):
        if self.v == 0:
            self.r = inf
        else:
            self.r = self.e / self.v
        
        return self.r
    
    # границы доверительного интервала

    def _bounds(self, number = 1):
        self.right = self.v + number * self.e
        self.left = self.v - number * self.e
        return (self.left, self.right)

    def _update(self):
        self._rel()
        self._bounds()


    # приведение числа к правильному количеству значащих цифр для погрешности




    @staticmethod
    def rounder(number = 0.0):
        if number != 0:
            S = str(float(number))
            point = S.find('.')
            for i in range(len(S)):
                if S[i] != '0' and S[i] != '.': 
                    idx = i
                    break

            if S[idx] == '1':
                S = S + '000'
                idx += 1
                if S[idx + 1] == '9':
                    if S[idx + 2] == '.':
                        if int(S[idx + 3]) >= 5:
                            idx -= 1
                    else:
                        if int(S[idx + 2]) >= 5:
                            idx -= 1
            
            return idx - point + (idx <= point)
        
        else: return 0

    def truncate(self):
        r = Value.rounder(self.e)
        return (round(self.v, r), round(self.e, r))
    
    # Пифагорово сложение

    @staticmethod
    def p(x, y): 
        return sqrt(x*x + y*y)
    
    # Нахождение величины по её доверительному интервалу

    @staticmethod
    def interval(x, y):
        v = (x + y)/2
        e = abs(x - y)/2
        return Value(v, e)
    # АРИФМЕТИЧЕСКИЕ ОПЕРАЦИИ

    # Сложение

    def __add__(self, other):
        if isinstance(other, Value):
            return Value(self.v + other.v, Value.p(self.e, other.e))
        if isinstance(other, int) or isinstance(other, float):
            return Value(self.v + other, self.e)
        return NotImplemented
    
    def __radd__(self, other):
        return self.__add__(other)
    
    # Вычитание

    def __sub__(self, other):
        if isinstance(other, Value):
            return Value(self.v - other.v, Value.p(self.e, other.e))
        if isinstance(other, int) or isinstance(other, float):
            return Value(self.v - other, self.e)
        return NotImplemented
    
    def __rsub__(self, other):
        if isinstance(other, (int, float)):
            return Value(other - self.v, self.e)
        return NotImplemented
    
    # Умножение

    def __mul__(self, other):
        if isinstance(other, Value):
            r1 = self.r
            r2 = other.r
            r = Value.p(r1, r2)
            v = self.v * other.v
            return Value(v, v * r)
        
        if isinstance(other, int) or isinstance(other, float):
            v = self.v * other
            return Value(v, v * self.r)
        return NotImplemented
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    # Деление

    def __truediv__(self, other):
        if isinstance(other, Value):
            if other.v == 0:
                raise ZeroDivisionError("Деление на ноль")
            r1 = self.r
            r2 = other.r
            r = Value.p(r1, r2)
            v = self.v / other.v
            return Value(v, v * r)
        
        if isinstance(other, int) or isinstance(other, float):
            if other == 0:
                raise ZeroDivisionError("Деление на ноль")
            v = self.v / other
            return Value(v, v * self.r)
        return NotImplemented
    
    def __rtruediv__(self, other):
        if self.v == 0:
            raise ZeroDivisionError("Деление на ноль")
        v = other / self.v
        return Value(v, v * self.r)
    
    # Отрицание

    def __neg__(self):
        return Value(-self.v, self.e)
    

    def __pow__(self, other):
        """Возведение в степень"""
        v = self.v ** other
        r = self.r * abs(other)
        return Value(v, v * r)
    

    def sqrt(self):
        """"Квадратный корень"""
        if self.v < 0:
            raise ValueError("Арифметический квадратный корень не определён")
        r = self.r/2
        v = sqrt(self.v)
        e = v * r
        return Value(v, e)
    

    def exp(self):
        """"Экспонента"""
        v = exp(self.v)
        return Value(v, v * self.e)

    def log(self):
        """Натуральный логарифм"""
        if self.v <= 0:
            raise ValueError("Логарифм не определён")
        v = log(self.v)
        return Value(v, self.r)
    
    def tan(self):
        """Тангенс (угол в радианах)"""
        v = tan(self.v)
        if self.cos() == 0:
            raise ValueError("Тангенс не определён")
        return Value(v, self.e / (cos(self.v)**2))
    
    def sin(self):
        """Синус (угол в радианах)"""
        v = sin(self.v)
        return Value(v, abs(cos(self.v)) * self.e)
    
    def cos(self):
        """Косинус (угол в радианах)"""
        v = cos(self.v)
        return Value(v, abs(sin(self.v)) * self.e)




    # СРАВНЕНИЕ

    def __eq__(self, other):
        if not isinstance(other, Value):
            return self.left <= other <= self.right
        return (self.left <= other.left <= self.right) or (self.left <= other.right <= self.right)
    
    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        if not isinstance(other, Value):
            return self.v < other and self != other
        return self.v < other.v and self != other
    
    def __le__(self, other):
        if not isinstance(other, Value):
            return self.v <= other or self == other
        return self.v <= other.v or self == other
    
    def __gt__(self, other):
        if not isinstance(other, Value):
            return self.v > other and self != other
        return self.v > other.v and self != other
    
    def __ge__(self, other):
        if not isinstance(other, Value):
            return self.v >= other or self == other
        return self.v >= other.v or self == other
    
    # Модуль

    def __abs__(self):
        return Value(abs(self.v), self.e)


    # Копирование

    def __copy__(self):
        return Value(self.v, self.e)

    def __deepcopy__(self, m):
        return Value(self.v, self.e)

import numpy as np
from copy import copy, deepcopy
import warnings as w 

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


@F_add
@G_add
class Data():

    def __init__(self, A = list(), E = 0):
        self.v_read(A)
        self.e_read(E)

    def v_read(self, A, erase = True):
        if isinstance(A, np.ndarray):
            V = deepcopy(A)

        elif isinstance(A, (list, tuple)):
            V = np.array(A)

        elif isinstance(A, (float, int)):
            V = np.array([A])

        else:
            raise TypeError(f"Unsupported type for reading: {type(A)}")

        if erase:
            self._v = V
        else:
            self._v = np.concatenate((self._v, V))
        
    
    def e_read(self, A, erase = True):
        if isinstance(A, np.ndarray):
            E = deepcopy(A)

        elif isinstance(A, (list,tuple)):
            E = np.array(A)

        elif isinstance(A, (int, float)):
            if hasattr(self, '_v'):
                E = np.zeros(len(self._v))
                E.fill(A)
            else:
                raise AttributeError("Array length is unknown")
            
        else:
            raise TypeError(f"Unsupported type for reading: {type(A)}")

        if erase:
            self._e = E
        else:
            self._e = np.concatenate((self._e, E))
    
    @property
    def v(self): return self._v

    @property
    def e(self): return self._e
    
    def __len__(self): 
        return self._v.size
               
    def read(self, 
             file_name, 
             col = 0, 
             e_col = None, 
             e = 0,
             ignore_first = False, 
             sep_col = None, 
             sep_dec = '', 
             erase = True):
        
        V = list()
        E = list()
        
        with open(file_name, 'r') as file:
            if ignore_first:
                s = file.readline()
                del s

            for line in file:
                row = line.split(sep_col)
                cell = row[col]
                for c in sep_dec:
                    cell = cell.replace(c, '.')
                V.append(float(cell))

                if e_col != None:
                    e_cell = row[e_col]
                    for c in sep_dec:
                        e_cell = e_cell.replace(c, '.')
                    E.append(float(e_cell))

        if e_col == None:
            E = [e]*len(V)
            
        self.v_read(V, erase)
        self.e_read(E, erase)

    def __str__(self):
        L = list()
        for i in range(len(self.v)):
            L.append(str(Value(self.v[i], self.e[i])))
        return(', '.join(L))
    
    def rand_e(self):
        return np.std(self.v)
    
    def sys_e(self):
        return self.e.max()
    
    def mean(self):
        E = (self.rand_e()**2 + self.sys_e()**2)**0.5
        E_mean = E / len(self)**0.5
        return Value(self.v.mean(), E_mean)
    
    def __invert__(self):
        return self.mean()
    

    def catch(self, d, rewrite = True):
        V = deepcopy(self.v)
        E = deepcopy(self.e)

        if len(self) == 0: return self
        prev = V[0]
        i = 1
        while i < len(V):
            if abs(V[i] - prev) >= d:
                V =  np.delete(V, i)
                E  = np.delete(E, i)
                continue
            prev = V[i]
            i += 1
        
        if rewrite:
            self.v_read(V)
            self.e_read(E)

        return Data(V, E)
    
    def __getitem__(self, index):
        if isinstance(index, slice):
            return Data(self.v[index], self.e[index])
        return Value(self.v[index], self.e[index])

    def __setitem__(self, index, value):
        if isinstance(value, Value):
            self.v[index] = value.v
            self.e[index] = value.e
        elif isinstance(value, (int, float)):
            self.v[index] = value
        else:
            raise TypeError(f"Unsupported type: {type(value)}")
        
    def zeroes(self, change = None):
        if change == None:
            return Data(np.nonzero(self.v), np.nonzero(self.e))
        new_v = self.v.copy()
        new_v[new_v == 0] = change
        return Data(new_v, self.e)
    
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

