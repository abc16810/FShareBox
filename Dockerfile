FROM tiangolo/uvicorn-gunicorn:python3.8-slim

LABEL Author="wsm" \
      E-mail="devopshot@163.com" 

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ 

COPY . /app

CMD ["gunicorn", "main:app", "-c", "/gunicorn_conf.py", "--log-config=logs.ini", "-k", "uvicorn.workers.UvicornH11Worker"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--log-config", "logs.ini"]