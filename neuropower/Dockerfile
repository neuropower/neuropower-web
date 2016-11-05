FROM oesteban/crn_nipype:freesurfer

# Update packages and install the minimal set of tools
RUN apt-get update && \
    apt-get install -y curl git xvfb bzip2 apt-utils

ENV LANG C.UTF-8

# Install pip
RUN pip install --upgrade pip && \
    pip install nose && \
    pip install numpy && \
    pip install scipy && \
    pip install pandas && \
    pip install matplotlib && \
    pip install xvfbwrapper

RUN mkdir /code

WORKDIR /code
ADD requirements.txt /code/

RUN conda install psycopg2 mpld3==0.2 scikit-learn==0.17.1 cycler==0.9.0 && \
  apt-get update && \
  apt-get install -y build-essential && \
  curl https://bootstrap.pypa.io/ez_setup.py -o - | python && \
  pip install -r requirements.txt && \
  apt-get install -y libglib2.0-0 && \
  apt-get install -y libfreetype6-dev libxft-dev && \
  pip install uwsgi && \
  pip install -U Jinja2

RUN pip install celery==3.0.19
RUN pip install --upgrade celery
RUN pip install SQLAlchemy
RUN pip install neuropower
RUN pip install django-celery
RUN pip install opbeat
RUN pip install django
RUN pip install django-crispy-forms
RUN pip install django-secure
RUN pip install django-sslserver
RUN conda install psycopg2
RUN pip install django-picklefield
RUN pip install matplotlib
RUN pip install palettable
RUN pip install mpld3
RUN pip install jinja2
RUN pip install sklearn
RUN pip install nilearn
RUN conda install sqlalchemy
RUN pip install kombu==3.0.30
RUN pip install redis && \
    pip install celery[redis] && \

env PATH=$PATH:/usr/lib/:/root/miniconda2/envs/crnenv/lib/
ADD shelve.py /root/miniconda2/envs/crnenv/bin/
ADD taps.p /code/

# Clear apt cache to reduce image size
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 3031
