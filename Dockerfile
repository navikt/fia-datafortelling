FROM python:3.9

COPY main.py .
COPY requirements.txt .

RUN pip3 install -r requirements.txt

CMD ["python3", "main.py"]