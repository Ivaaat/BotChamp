FROM python:latest
ENV PYTHONUNBUFFERED=1
WORKDIR /apps
RUN apt-get clean && apt-get update && apt-get install -y locales
RUN localedef -i ru_RU -c -f UTF-8 -A /usr/share/locale/locale.alias ru_RU.UTF-8
RUN pip install --upgrade pip
COPY requirements.txt /apps/
RUN pip3 install -r /apps/requirements.txt