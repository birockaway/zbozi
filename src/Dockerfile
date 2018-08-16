FROM ubuntu:16.04

RUN apt-get update && \
    apt-get install -y python3 python3-pip curl chromium-browser && \
    rm -rf /var/lib/apt/lists/* && \
    curl https://chromedriver.storage.googleapis.com/2.40/chromedriver_linux64.zip -o ~/chromedriver.zip && \
    python3 -m zipfile -e ~/chromedriver.zip /usr/local/bin/ && \
    chmod a+x /usr/local/bin/chromedriver && \
    rm ~/chromedriver.zip

RUN pip3 install --upgrade --no-cache-dir \
    selenium~=3.0 \
    requests~=2.19.0 \
    pandas~=0.23.0 

RUN apt-get update && apt-get install -y git

RUN apt-get install python3.5

WORKDIR /home


RUN pip3 uninstall -y numpy 
RUN pip3 install numpy==1.14.5


# Install keboola docker
RUN pip3 install git+git://github.com/keboola/python-docker-application.git #v0.1   

RUN git clone https://github.com/birockaway/zbozi.git ./ #v 1.0.43


ENTRYPOINT python3 -u ./src/selen.py



