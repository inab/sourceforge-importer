FROM ubuntu

COPY . ./

RUN chmod 1777 /tmp
RUN apt-get upgrade -y 
RUN apt-get update -y
RUN apt-get install -y python3-pip

RUN pip install --no-cache-dir -r requirements.txt

CMD python3 ./main.py -l=DEBUG

