FROM tiangolo/meinheld-gunicorn-flask:python3.7
RUN curl -fsSL https://get.docker.com/ | sh
COPY ./requirements.txt /app
COPY ./main.py /app
COPY ./prestart.sh /app
COPY ./tunnel_rpc /app/tunnel_rpc
