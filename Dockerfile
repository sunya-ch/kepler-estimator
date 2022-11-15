FROM python:3.8

WORKDIR /usr/src/app
RUN mkdir -p src
COPY src src

CMD ["python", "src/estimator.py"]