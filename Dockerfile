FROM python:3
RUN touch /var/log/access.log
WORKDIR /usr/src
ADD . /usr/src
ENTRYPOINT ["python", "log-watch.py"]
