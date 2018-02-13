FROM neuropower/neurodesign
MAINTAINER Joke Durnez <joke.durnez@gmail.com>

RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


# get neuropower from github repo
RUN apt-get install git
WORKDIR /tmp
RUN git clone -b awsbatch https://github.com/neuropower/neuropower-web.git

# add requirements

RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
RUN pip install django-storages
RUN pip install django-cors-headers

# add script to run batch
ADD fetch_and_run.sh /usr/local/bin/fetch_and_run.sh

# add local genetic algorithm
ADD neurodesign.py /usr/local/bin/

ENV LD_LIBRARY_PATH=/opt/conda/lib:$LD_LIBRARY_PATH

RUN pip install awscli==1.14.19
#RUN chmod +x ~/.local/bin/aws
#ENV PATH=/root/.local/bin:$PATH

ENTRYPOINT ["/usr/local/bin/fetch_and_run.sh"]
