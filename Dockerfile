#Dockerfile
FROM alpine:latest 
WORKDIR /emqtt_export
COPY . /emqtt_export/
RUN apk update && \
    apk add curl python3 && \
    pip3 install prometheus_client requests
EXPOSE 9214
CMD ["/bin/sh","run.sh"]