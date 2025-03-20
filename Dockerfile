FROM python:3.12-slim

RUN apt-get update
RUN pip install --no-cache-dir "poetry==1.8.3"


COPY poetry.lock pyproject.toml app/

WORKDIR /app

RUN poetry config virtualenvs.create false & poetry install

COPY . /app

CMD ["python", "app/main.py"]
