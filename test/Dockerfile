FROM python:3.6.2-alpine

RUN mkdir -p /eval
WORKDIR /eval
ADD . /eval/

RUN pip install -r requirements.txt
RUN tar xvjf data.tar.bz2
RUN bunzip2 -f test/example.pred.dev.jsonl.bz2

CMD python /eval/evaluate.py /eval/data/dev.jsonl /eval/data/dev.db /eval/test/example.pred.dev.jsonl
