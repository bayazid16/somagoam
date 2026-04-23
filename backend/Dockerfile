FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


WORKDIR /app


RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt


COPY . /app/

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]


EXPOSE 8000