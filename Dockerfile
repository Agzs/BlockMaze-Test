FROM ubuntu:16.04
WORKDIR /root
COPY geth /usr/bin/geth
COPY passfile /root/
COPY prfKey /usr/local/prfKey         
COPY ./zklib/lib* /usr/local/lib/     
RUN apt-get update && apt-get install -y --reinstall ca-certificates \
    && echo "deb http://mirrors.aliyun.com/ubuntu/ xenial main restricted" > /etc/apt/sources.list \   
    && echo "deb http://mirrors.aliyun.com/ubuntu/ xenial-updates main restricted" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/ubuntu/ xenial universe" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/ubuntu/ xenial-updates universe" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/ubuntu/ xenial multiverse" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/ubuntu/ xenial-updates multiverse" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/ubuntu/ xenial-backports main restricted universe multiverse" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/ubuntu/ xenial-security main restricted" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/ubuntu/ xenial-security universe" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/ubuntu/ xenial-security multiverse" >> /etc/apt/sources.list \
    && apt-get clean && apt-get update \
    && apt-get -o Acquire::https::No-Cache=True -o Acquire::http::No-Cache=True update \
    && apt-get install -y --fix-missing build-essential cmake git libgmp3-dev libprocps4-dev python-markdown libboost-all-dev libssl-dev pkg-config
EXPOSE 8545 8546 30303
#ENTRYPOINT [ "geth" ]
