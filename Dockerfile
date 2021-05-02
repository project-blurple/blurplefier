FROM public.ecr.aws/lambda/python:3.8

ADD requirements.txt /var/task/
RUN pip install -r requirements.txt

ADD app.py magic.py /var/task/

CMD ["app.handler"]
