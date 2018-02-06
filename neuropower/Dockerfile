# Use Ubuntu 16.04 LTS
FROM ubuntu:xenial-20161213

# Pre-cache neurodebian key
COPY docker/neurodebian.gpg /root/.neurodebian.gpg

# Prepare environment
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
                    curl \
                    bzip2 \
                    ca-certificates \
                    xvfb \
                    build-essential \
                    autoconf \
                    libtool \
                    pkg-config && \
    curl -sSL http://neuro.debian.net/lists/xenial.us-ca.full >> /etc/apt/sources.list.d/neurodebian.sources.list && \
    apt-key add /root/.neurodebian.gpg && \
    (apt-key adv --refresh-keys --keyserver hkp://ha.pool.sks-keyservers.net 0xA5D32F012649A5A9 || true) && \
    apt-get update

ENV FSL_DIR=/usr/share/fsl/5.0 \
    OS=Linux \
    FS_OVERRIDE=0 \
    FIX_VERTEX_AREA= \
    FSF_OUTPUT_FORMAT=nii.gz

# Installing Neurodebian packages (FSL, AFNI, git)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
                    fsl-core=5.0.9-4~nd16.04+1 \
                    fsl-mni152-templates=5.0.7-2

ENV FSLDIR=/usr/share/fsl/5.0 \
    FSLOUTPUTTYPE=NIFTI_GZ \
    LD_LIBRARY_PATH=/usr/lib/fsl/5.0:$LD_LIBRARY_PATH
ENV PATH=/usr/lib/fsl/5.0:$PATH

RUN echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    apt-get install wget && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda2-4.3.31-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh

ENV PATH /opt/conda/bin:$PATH

RUN conda config --add channels conda-forge

RUN conda install numpy=1.12.0 && \
    conda install scipy=0.18.1 && \
    conda install pandas=0.19.2 && \
    conda install matplotlib=2.0.0

ENV LD_LIBRARY_PATH=/opt/conda/lib:$LD_LIBRARY_PATH

# Clear apt cache to reduce image size
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir /code

WORKDIR /code
ADD requirements.txt /code/

RUN conda install psycopg2 mpld3==0.2 scikit-learn==0.17.1 cycler && \
  apt-get update && \
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
ENV PATH=/usr/lib/python2.7:$PATH
