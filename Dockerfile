FROM python:3.7
ENV VIZUALISER_ENV production
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
