import subprocess

heroku_project_name = input('What is the name of the heroku project? ').strip()

with open('.env') as f:
    env_vars = [(line.strip().replace('export ', '').split('=', 1)) for line in f.readlines()]

command = ['heroku', 'config:set', ' '.join([f'{k}={v}' for k, v in env_vars]), '-a {heroku_project_name}']
print(' '.join(command))