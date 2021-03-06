# Developer Student Clubs Portal

## Requirements
- Python 3.8.x
- Django 3.x.x
- [pipenv](https://github.com/pypa/pipenv#installation) (`pip install pipenv`)
- SQLite

## Installation
- Clone the repo with `git clone https://github.com/DSC-RPI/dsc-portal.git`
- Run `pipenv shell` in the terminal in the repo folder
- Install the required packages with `pipenv install`
- Copy the `.env` given by a DSC Lead into the root folder
  - The required keys and format are in `.env.example` if you'd like to setup your own
- Run `source .env`
- Run migrations with `python manage.py migrate`
  - You might need to make them first with `python manage.py makemigrations`
- Run locally with `python manage.py runserver`