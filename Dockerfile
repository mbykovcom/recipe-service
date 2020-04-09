FROM python:3.7

RUN mkdir -p /usr/src/app
RUN mkdir -p /usr/src/images
COPY . /usr/src/app
WORKDIR /usr/src/app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80