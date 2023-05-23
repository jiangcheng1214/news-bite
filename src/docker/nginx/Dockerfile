FROM openresty/openresty:alpine

RUN mkdir /var/www
COPY ./nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY ./www/ /var/www/

CMD ["/usr/local/openresty/bin/openresty", "-g", "daemon off;"]