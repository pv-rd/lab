file = open('text.txt')
A = [int(line) for line in file]
file.close()

N = 4000 

T = 10 # интервал разбиения

B = [] # результирующий список

s = 0
for i in range(N): # разбиение
    s+=A[i]
    if (i+1)%T==0:
        B.append(s)
        s = 0

file_res = open('res.txt', 'w')

for b in B:
    print(b, file=file_res)

file_res.close()



