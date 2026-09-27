from math import inf, sqrt, exp, log, sin, cos, tan, floor, log10

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
