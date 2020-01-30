# Developer Student Clubs Portal

## Requirements
- Python 3.8.x
- [pipenv](https://github.com/pypa/pipenv#installation)
- SQLite

## Installation
- Clone the repo with `git clone https://github.com/DSC-RPI/dsc-portal.git`
- Run `pipenv shell` in the terminal in the repo folder
- Copy the `.env` given by a DSC Lead into the root folder
- Run `source .env`
- Make migrations with `python manage.py migrate`
- Run locally with `python manage.py runserver`

