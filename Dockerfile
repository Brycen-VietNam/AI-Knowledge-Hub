FROM python:3.12-slim

WORKDIR /app

# System dependencies — MeCab (Japanese tokenizer, cjk-tokenizer WARN-01)
# DevOps review required before merge per checklist WARN-01
# libmagic1 added for MIME/magic-byte validation (document-parser WARN-02 resolution)
RUN apt-get update && apt-get install -y --no-install-recommends \
    mecab \
    libmecab-dev \
    mecab-ipadic-utf8 \
    libmagic1 \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /usr/local/etc \
 && ln -s /etc/mecabrc /usr/local/etc/mecabrc

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

EXPOSE 8000
CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
