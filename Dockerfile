FROM ubuntu:18.04
MAINTAINER pablo.de.andres@fraunhofer.iwm.de

RUN apt-get update && \
    apt-get install -y python3.7 python3-pip
RUN python3.7 -m pip install --upgrade pip

RUN ln -s /usr/bin/python3.7 /usr/bin/python & \
    ln -s /usr/bin/pip3 /usr/bin/pip

ADD . /simphony/osp-core
WORKDIR /simphony/osp-core

RUN pip install tox
RUN tox -e py37
RUN python setup.py install