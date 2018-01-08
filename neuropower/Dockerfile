FROM oesteban/crn_nipype:freesurfer

# Update packages and install the minimal set of tools
RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get install -y curl git xvfb bzip2 apt-utils
ENV LANG C.UTF-8

# Install conda
RUN conda install nose && \
    conda install numpy && \
    conda install scipy && \
    conda install pandas && \
    conda install matplotlib && \
    conda install xvfbwrapper

RUN mkdir /code

WORKDIR /code
ADD requirements.txt /code/

RUN conda install psycopg2 mpld3==0.2 scikit-learn==0.17.1 cycler && \
  apt-get update && \
  apt-get install -y build-essential && \
  curl https://bootstrap.pypa.io/ez_setup.py -o - | python && \
  apt-get install -y libglib2.0-0 && \
  apt-get install -y libfreetype6-dev libxft-dev && \
  conda install uwsgi && \
  conda install Jinja2 && \
  conda install celery && \
  conda install SQLAlchemy && \
  conda install django-celery

RUN pip install -r requirements.txt
RUN pip install awscli --upgrade --user

# Clear apt cache to reduce image size
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV PATH=~/.local/bin:$PATH
