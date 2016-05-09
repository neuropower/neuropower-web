FROM oesteban/crn_nipype

RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN source activate crnenv && \
  conda install psycopg2 mpld3==0.2 scikit-learn==0.17.1 && \
  conda uninstall pyparsing wheel jinja2 && \
  pip install -r requirements.txt && \
  apt-get install -y build-essential && \
  apt-get install -y libglib2.0-0 && \
  apt-get install -y libfreetype6-dev libxft-dev && \
  pip install -U uwsgi && \
  pip install -U Jinja2

EXPOSE 3031
