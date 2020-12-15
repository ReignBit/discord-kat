FROM python:3.7.9-buster

WORKDIR /usr/src/app


COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install requests

COPY . .
CMD [ "python", "-m", "bot" ]
