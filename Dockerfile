FROM ubuntu:18.04
LABEL org.opencontainers.image.authors="pablo.de.andres@fraunhofer.iwm.de, jose.manuel.dominguez@iwm.fraunhofer.de, yoav.nahshon@iwm.fraunhofer.de"

RUN apt-get update && \
    apt-get install -y python3.7 python3-pip
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.6 1
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.7 2
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 2
RUN python -m pip install --upgrade pip

ADD . /simphony/simphony-osp
RUN pip install /simphony/simphony-osp