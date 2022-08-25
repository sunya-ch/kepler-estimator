FROM python:3.7

WORKDIR /usr/src/app
RUN mkdir -p src
COPY src src
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

CMD ["python", "src/estimator.py"]