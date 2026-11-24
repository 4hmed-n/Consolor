test = 'echo Test1 &  & echo Test2'
print('Before:', repr(test))
while ' &  & ' in test:
    test = test.replace(' &  & ', ' & ')
print('After:', repr(test))
