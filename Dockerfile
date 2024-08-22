FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

WORKDIR /app
COPY . /app

EXPOSE 15000
CMD python3 usebounce.py
