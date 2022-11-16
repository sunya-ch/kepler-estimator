FROM ghcr.io/sunya-ch/kepler-estimator-base:latest

WORKDIR /usr/src/app
COPY src src

CMD ["python", "src/estimator.py"]