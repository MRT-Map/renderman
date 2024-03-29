FROM python:3.11-slim

COPY . .

RUN apt update; apt-get install -y git

RUN pip install -U pip; pip install .; pip cache purge

VOLUME ["/vol"]

ENV DOCKER=true
CMD python -m renderman
EXPOSE 8000
