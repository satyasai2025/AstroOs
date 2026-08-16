with open('apps/web/src/config/navConfig.ts', 'rb') as f:
    data = f.read()
print('size', len(data))
try:
    data.decode('utf-8')
    print('UTF-8 ok')
except UnicodeDecodeError as e:
    print('Error at', e.start, ':', repr(data[e.start:e.start+10]))
    print('hex', data[e.start:e.start+10].hex())
    # Show more context
    start = max(0, e.start - 50)
    end = min(len(data), e.start + 50)
    print('Context:', data[start:end])