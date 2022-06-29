FROM python:3.10
LABEL org.opencontainers.image.authors="simphony@fraunhofer.iwm.de"

ADD . /simphony/simphony-osp
RUN pip install /simphony/simphony-osp
