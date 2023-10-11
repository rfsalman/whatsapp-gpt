FROM python:3.11

ENV PYTHONUNBUFFERED True

WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY ./src ./src/

EXPOSE 8000
CMD ["uvicorn",  "src.main:app" , "--reload"]
