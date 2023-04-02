# Project Title

News API build in DRF (Django REST Framework)

## Table of Contents

- [Project Title](#project-title)
  - [Table of Contents](#table-of-contents)
  - [About the Project](#about-the-project)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
  - [Usage](#usage)
  - [Contributing](#contributing)
  - [License](#license)
  - [Contact](#contact)

## About the Project

Get News data from API or crawller 

## Getting Started

cd /path/to/backend

python manage.py runserver

### Prerequisites

Python 3.10+

Mysql 5.8+ server

Redis 4.0+

Rabbitmq server latest

Nginx(To Do)

Monitor(To Do)

### Installation

cd /path/to/backend
pip install -r requirements.txt

## Usage

Command:
cd /path/to/backend

[获取新闻数据]

python manage.py get_news_list

[启动 News Consume]

python manage.py news_consumer

[crontab]

python manage.py crontab --help

python manage.py crontab add

python manage.py crontab show

python manage.py crontab remove

....

## Contributing

Waiting to update

## License

MIT

## Contact

talhuang1231@gmail.com