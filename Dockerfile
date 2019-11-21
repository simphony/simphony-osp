FROM python:3.8
RUN apt-get update
ADD . /simphony/osp-core
WORKDIR /simphony/osp-core

RUN cat requirements.txt | xargs -n 1 -L 1 pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org; echo 1
RUN python setup.py install
