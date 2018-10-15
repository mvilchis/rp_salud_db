FROM alpine:3.7

RUN apk add --no-cache \
        uwsgi-python3 \
        python3

COPY requirements.txt /app/


WORKDIR /app

RUN pip3 install -r requirements.txt

COPY . /app

EXPOSE 5000

ENTRYPOINT ["bash"]
CMD ["./start.sh"]
