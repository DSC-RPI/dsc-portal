import subprocess
from time import sleep

with open('.env') as f:
    env_vars = [(line.strip().replace('export ', '').split('=', 1)) for line in f.readlines()]

command = ['heroku', 'config:set', ' '.join([f'{k}={v}' for k, v in env_vars]), '-a dsc-rpi']
print(' '.join(command))