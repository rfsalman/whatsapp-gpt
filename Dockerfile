FROM python:3.11

ENV PYTHONUNBUFFERED True

WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r ./requirements.txt
RUN pip install weaviate-client

COPY ./src ./src/

EXPOSE 8000
CMD ["uvicorn",  "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
