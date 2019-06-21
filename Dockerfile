FROM python:3.7
ADD . /code/libs
WORKDIR /code/libs

RUN pip install -r requirements.txt  --trusted-host pypi.org --trusted-host files.pythonhosted.org
RUN python setup.py install
