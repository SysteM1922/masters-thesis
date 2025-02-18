FROM ubuntu:24.10

RUN apt update && apt upgrade -y
RUN apt install nginx libnginx-mod-rtmp -y

EXPOSE 1935 5555

COPY nginx.conf /etc/nginx/nginx.conf

CMD ["nginx", "-g", "daemon off;"]