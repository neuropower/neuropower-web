FROM neuropower/neurodesign
MAINTAINER Joke Durnez <joke.durnez@gmail.com>

RUN apt-get install git
WORKDIR /tmp
RUN git clone -b awsbatch https://github.com/neuropower/neuropower-web.git

RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt

RUN pip install django-storages
RUN pip install django-cors-headers

ADD fetch_and_run.sh /usr/local/bin/fetch_and_run.sh
USER nobody
ENV LD_LIBRARY_PATH=/opt/conda/lib:$LD_LIBRARY_PATH
ENV PATH=~/.local/bin:$PATH

ENTRYPOINT ["/usr/local/bin/fetch_and_run.sh"]
