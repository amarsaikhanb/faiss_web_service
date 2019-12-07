FROM continuumio/miniconda3:latest

RUN mkdir /opt/faiss_web_service
WORKDIR /opt/faiss_web_service

RUN mkdir log

COPY requirements.txt .
COPY condarc /root/.condarc

RUN conda install -y -c pytorch faiss-cpu
RUN conda install -y -c conda-forge --file requirements.txt

COPY bin bin
COPY src src

ENTRYPOINT ["bin/faiss_web_service.sh"]
