from math import *
file = open('res.txt')
A = [int(line) for line in file]
file.close()

N = len(A)

# гистограмма

S = set()
for x in A:
    S.add(x)

gist = open('gist.txt', 'w')
for s in S:
    c = 0
    for x in A:
        if (x==s):
            c+=1
    w = c/N
    print(s, w, file=gist)
gist.close()

# график среднего и стандартного отклонения от номера измерения

B = []
sr = open('sr.txt', 'w')
for x in A:
    B.append(x)
    X = sum(B)/len(B)
    D = 0.0
    for b in B:
        D+=(b-X)**2
    D /= len(B)
    s = sqrt(D)

    
    print(X, s, file=sr)
    










