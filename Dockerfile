FROM python:3.8-alpine


COPY . ./

RUN chmod 1777 /tmp
# need git to install dependencies
RUN apt-get upgrade -y 
RUN apt-get update -y
RUN apt-get install -y python3-pip

RUN pip3 install -r ./requirements.txt


CMD python3 ./main.py

