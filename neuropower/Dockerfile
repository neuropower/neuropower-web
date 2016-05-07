FROM oesteban/crn_base

# System packages
RUN apt-get update && apt-get install -y curl

# Install FSL
RUN curl -sSL http://neuro.debian.net/lists/vivid.de-m.full | tee /etc/apt/sources.list.d/neurodebian.sources.list && \
    curl -sSL http://neuro.debian.net/lists/vivid.us-tn.full >> /etc/apt/sources.list.d/neurodebian.sources.list && \
    apt-key adv --recv-keys --keyserver hkp://pgp.mit.edu:80 0xA5D32F012649A5A9 && \
    apt-get update && \
    apt-get install -y fsl-5.0-core fsl-core && \
    echo 'source /etc/fsl/fsl.sh' >> /root/.bashrc

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
                       libjpeg-dev \
                       libyaml-dev

# Clear apt cache to reduce image size
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /root

# Install miniconda
RUN curl -sSLO https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh && \
    /bin/bash Miniconda-latest-Linux-x86_64.sh -b -p /usr/local/miniconda2 && \
    rm Miniconda-latest-Linux-x86_64.sh && \
    echo '#!/bin/bash' >> /etc/profile.d/anaconda.sh && \
    echo 'export PATH=/usr/local/miniconda2/bin:$PATH' >> /etc/profile.d/anaconda.sh

ENV PATH /usr/local/miniconda2/bin:$PATH

RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN conda install scipy==0.17.0 pandas==0.17.1 numpy==1.10.4 psycopg2 mpld3==0.2 scikit-learn==0.17.1
RUN conda uninstall pyparsing wheel jinja2 sklearn

RUN pip install -r requirements.txt
RUN apt-get update
RUN apt-get install -y build-essential
RUN apt-get install -y libglib2.0-0
RUN apt-get install -y libfreetype6-dev libxft-dev
RUN pip --no-cache-dir install -U matplotlib
RUN pip install -U uwsgi
RUN pip install -U Jinja2
RUN pip install -U sklearn

EXPOSE 3031
