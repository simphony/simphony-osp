FROM python:3.8
RUN apt-get update
ADD . /simphony/osp-core
WORKDIR /simphony/osp-core

RUN pip install -r requirements.txt  --trusted-host pypi.org --trusted-host files.pythonhosted.org
RUN python setup.py install -c
