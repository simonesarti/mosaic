FROM nvcr.io/nvidia/tensorflow:23.02-tf2-py3

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y gdal-bin
RUN apt-get install -y libgdal-dev
RUN export CPLUS_INCLUDE_PATH=/usr/include/gdal && export C_INCLUDE_PATH=/usr/include/gdal && pip install GDAL

RUN mkdir /.config
RUN chmod 777 /.config

RUN mkdir /.local
RUN chmod 777 /.local

RUN mkdir /.cache
RUN chmod 777 /.cache

COPY . /opt/ml/code/
RUN cd /opt/ml/code/  && pip install -e .
WORKDIR /opt/ml/code/