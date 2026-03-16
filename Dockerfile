FROM python:3.10-slim

COPY . ./

RUN python3 -m pip install --no-cache-dir -r requirements.txt

CMD python3 ./main.py -l=DEBUG

