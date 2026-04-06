FROM python:3.12-slim

WORKDIR /app

# System dependencies — MeCab (Japanese tokenizer, cjk-tokenizer WARN-01)
# DevOps review required before merge per checklist WARN-01
RUN apt-get update && apt-get install -y --no-install-recommends \
    mecab \
    libmecab-dev \
    mecab-ipadic-utf8 \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /usr/local/etc \
 && ln -s /etc/mecabrc /usr/local/etc/mecabrc

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

EXPOSE 8000
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
