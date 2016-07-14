#!/usr/bin/python
tmp = ['a', 'b', 'b', 'b', 'a', 'b']
num = 0

while num < len(tmp):
    print(num, tmp[num])
    if tmp[num] == 'b':
        tmp[num - 1] += 'b'
        del tmp[num]
    else:
        num += 1
    print(tmp)
