FROM continuumio/miniconda3
MAINTAINER matthias.urban@fraunhofer.iwm.de

RUN apt-get update
ADD . /simphony/osp-core
WORKDIR /simphony/osp-core

RUN pip install tox tox-conda
RUN tox -e py37
RUN python setup.py install