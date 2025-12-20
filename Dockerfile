
FROM python:alpine

WORKDIR /apiventory
COPY LICENSE.md /apiventory
COPY requirements.txt /apiventory
COPY main.py /apiventory
COPY src /apiventory/src

RUN pip install -r requirements.txt

CMD ["python", "-m", "main"]