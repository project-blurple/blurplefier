FROM public.ecr.aws/lambda/python:3.8

ADD requirements.txt app.py magic.py /var/task/
RUN pip install -r requirements.txt

CMD ["app.handler"]
