FROM continuumio/miniconda
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN conda install scipy==0.17.0 pandas==0.17.1 numpy==1.10.4 matplotlib==1.5.1 psycopg2 mpld3==0.2 scikit-learn==0.17.1
RUN conda uninstall pyparsing wheel jinja2 sklearn

RUN pip install -r requirements.txt
RUN apt-get install -y build-essential
RUN pip install uwsgi
RUN pip install -U Jinja2
RUN pip install -U sklearn

EXPOSE 3031
