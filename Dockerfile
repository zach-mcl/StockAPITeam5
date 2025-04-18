FROM python:3.10-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential python3-dev libyaml-dev && \
    rm -rf /var/lib/apt/lists/*

COPY . .

ENV FLASK_APP=app.py FLASK_ENV=production
EXPOSE 4000:5000
CMD ["flask", "run", "--host=0.0.0.0"]