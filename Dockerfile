FROM python:3.7
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV VIZUALISER_ENV production
EXPOSE 5000
CMD [ "python", "./main.py" ]
