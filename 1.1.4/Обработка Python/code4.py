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

c1 = c2 = c3 = 0

for x in A:
    if (abs(x-X) <= s):
        c1+=1
    if (abs(x-X) <= 2*s):
        c2+=1
    if (abs(x-X) <= 3*s):
        c3+=1

w1 = c1 / N * 100
w2 = c2 / N * 100
w3 = c3 / N * 100



print(w1)
print(w2)
print(w3)








