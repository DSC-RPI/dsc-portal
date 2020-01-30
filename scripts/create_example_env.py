with open('.env') as f:
  pairs = [line.strip().split('=', 1) for line in f.readlines()]

with open('.env.example', 'w') as f:
  for key, value in pairs:
    f.write(f'export {key}=XXXXXXXXXXXXXXX\n')

print('Update .env.example')