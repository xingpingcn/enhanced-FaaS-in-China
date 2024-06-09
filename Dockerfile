FROM python:3.11
WORKDIR /bin/enhanced-faas
COPY ./requirements.txt ./
RUN pip install -r ./requirements.txt
ENTRYPOINT [ "python" ]
CMD [ "test.py" ]