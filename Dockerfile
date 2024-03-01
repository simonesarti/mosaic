FROM nvcr.io/nvidia/tensorflow:23.02-tf2-py3

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update --fix-missing
RUN apt install -y gdal-bin
RUN apt install -y libgdal-dev
RUN export CPLUS_INCLUDE_PATH=/usr/include/gdal && export C_INCLUDE_PATH=/usr/include/gdal && pip install GDAL
RUN apt clean

# create necessary directories and give write permission
RUN mkdir /.config
RUN mkdir /.local
RUN mkdir /.cache

RUN chmod -R 777 /.config
RUN chmod -R 777 /.local
RUN chmod -R 777 /.cache

# Set the working directory
WORKDIR /opt/mosaic

# Create folder where to save intermediate tifs
RUN mkdir ./tmp_images

# Copy and install requirements 
# executed ONLY if requirements have changed
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the project files into the working directory (except those in .dockerignore)
# Executed when the code changes
COPY . .
