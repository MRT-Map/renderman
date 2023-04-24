FROM python:3.11

COPY . .

RUN pip install -U pip
RUN pip install .

VOLUME ["/vol"]

ENV DOCKER=true
CMD python -m renderman
EXPOSE 8000