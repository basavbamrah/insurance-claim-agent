FROM python:3.11.0-bullseye

EXPOSE 5000/tcp

WORKDIR /app

COPY . .

COPY requirements.txt requirements.txt
EXPOSE 5000/tcp

RUN pip install --default-timeout=6000 -r requirements.txt

RUN apt-get update
RUN apt-get install -y libmagic-dev libreoffice poppler-utils tesseract-ocr
ENV AZURE_OPENAI_API_KEY="key"
ENV AZURE_OPENAI_ENDPOINT="endpoint"
ENV AZURE_OPENAI_API_VERSION="version"
ENV AZURE_OPENAI_CHAT_DEPLOYMENT_NAME="model"

CMD ["gunicorn", "-b", "0.0.0.0:5000", "--timeout", "600", "app:app", "--workers", "4"]