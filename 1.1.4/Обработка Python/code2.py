from math import *
file = open('res_10.txt')
A = [int(line) for line in file]
file.close()

N = len(A)

S = set()
for a in A:
    S.add(a)

m = sum(A)/len(A) # среднее

ss = sqrt(m) 

f = open('r.txt', 'w')

for s in S:
    c = 0
    for a in A:
        if a == s:
            c+=1

    w = c/N

    p = (m**s) * (e**(-m)) / factorial(s) # распределение Пуассона

    g = e**(-(s-m)**2 / (2*ss**2)) / (ss*sqrt(2*3.14)) #распределение Гаусса
    
    print(s, w, p, g, file = f)

f.close()


