FROM ubuntu:vivid

RUN ln -snf /bin/bash /bin/sh

# Update packages and install the minimal set of tools
RUN apt-get update && \
    apt-get install -y curl git xvfb bzip2 apt-utils

# Enable neurodebian
RUN curl -sSL http://neuro.debian.net/lists/vivid.de-m.full | tee /etc/apt/sources.list.d/neurodebian.sources.list && \
    curl -sSL http://neuro.debian.net/lists/vivid.us-tn.full >> /etc/apt/sources.list.d/neurodebian.sources.list && \
    apt-key adv --recv-keys --keyserver hkp://pgp.mit.edu:80 0xA5D32F012649A5A9 && \
    apt-get update && \
    apt-get install -y fsl-core afni && \
    echo 'source /etc/fsl/fsl.sh' >> /etc/profile.d/crn_neuro.sh && \
    echo 'source /etc/afni/afni.sh' >> /etc/profile.d/crn_neuro.sh

# Install debian dependencies of python packages
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y graphviz \
                       pandoc &&\
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /root

RUN curl -sSLO https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh && \
    /bin/bash Miniconda-latest-Linux-x86_64.sh -b && \
    rm Miniconda-latest-Linux-x86_64.sh
ENV PATH /root/miniconda2/bin:$PATH

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

# Create conda environment
RUN conda create -y -n crnenv lockfile && \
    echo 'source activate crnenv' >> /root/.bashrc

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y gfortran \
                       liblapack-dev \
                       libblas-dev \
                       libatlas-dev \
                       libatlas-base-dev \
                       libblas3 \
                       libblas-common \
                       libopenblas-dev \
                       libxml2-dev \
                       libxslt1-dev \
                       libfreetype6-dev \
                       libpng12-dev \
                       libqhull-dev \
                       libxft-dev \
                       libjpeg-dev

# Clear apt cache to reduce image size
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install pip
RUN source activate crnenv && \
    pip install --upgrade pip && \
    pip install nose && \
    pip install numpy && \
    pip install scipy && \
    pip install pandas && \
    pip install matplotlib && \
    pip install xvfbwrapper

# Install nipype & mriqc
RUN mkdir -p src && \
    cd src && \
    git clone https://github.com/nipy/nipype.git && \
    source activate crnenv && \
    cd nipype && \
    pip install -e .

RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN source activate crnenv && \
  conda install psycopg2 mpld3==0.2 scikit-learn==0.17.1 cycler==0.9.0 && \
  apt-get update && \
  apt-get install -y build-essential && \
  curl https://bootstrap.pypa.io/ez_setup.py -o - | python && \
  pip install -r requirements.txt && \
  apt-get install -y libglib2.0-0 && \
  apt-get install -y libfreetype6-dev libxft-dev && \
  pip install uwsgi && \
  pip install -U Jinja2

RUN pip install celery[redis]
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
RUN pip install redis

# Clear apt cache to reduce image size
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 3031
