s = 'echo "Test" & python "D:\\New folder\\consolor.py" blur & echo "Done"'
parts = s.split('&')
print('Parts:', parts)
filtered = [p.strip() for p in parts if p.strip() and not ('blur' in p and 'consolor' in p)]
print('Filtered:', filtered)
result = ' & '.join(filtered)
print('Result before cleanup:', repr(result))

# Clean up double ampersands
while ' &  & ' in result:
    result = result.replace(' &  & ', ' & ')
print('Result after cleanup:', repr(result))
