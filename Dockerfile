FROM python:3.9-slim-buster

RUN mkdir /src
WORKDIR /src

# install python dependencies
COPY src/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
COPY src .
ENTRYPOINT ["/src/entrypoint.sh"]