from math import *
file = open('res_80.txt')
A = [int(line) for line in file]
file.close()

T = 80 # разбиение

N = len(A)
X = sum(A)/N

D = 0.0 # дисперсия
for x in A:
    D += (x-X)**2
D /= N 

s = sqrt(D) # стандартное отклонение

ss = s/sqrt(N) # погрешность среднего

j = X/T # средняя интенсивность

J = [x/T for x in A]

Dj = 0.0 
for x in J:
    Dj += (x-j)**2
Dj /= N
sj = sqrt(Dj)
ssj = sj/sqrt(N) # погрешность интенсивности

print("Среднее: ", X)
print("Дисперсия: ", D)
print("Стандартное отклонение: ", s)
print("Погрешность среднего: ", ss)
print("Средняя интенсивность: ", j)
print("Погрешность интенсивности: ", ssj)






