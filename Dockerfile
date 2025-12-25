FROM python:3.11

RUN mkdir /fastapi

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .


CMD python -m api.main