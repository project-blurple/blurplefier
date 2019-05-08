FROM python:3.7-alpine AS requirements
ADD requirements.txt .
RUN apk add --no-cache libffi-dev gcc zlib-dev jpeg-dev freetype-dev libwebp libwebp-dev musl-dev
RUN pip install -r requirements.txt

FROM python:3.7-alpine
RUN apk add --no-cache jpeg-dev libwebp libwebp-dev
WORKDIR /blurple
COPY --from=requirements /usr/local/lib/python3.7/site-packages /usr/local/lib/python3.7/site-packages
RUN adduser -D -h /app -s /bin/sh -u 1000 blurple
COPY --chown=1000 . .
USER blurple
