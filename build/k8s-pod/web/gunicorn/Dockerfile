# Copyright (c) [2022] Huawei Technologies Co.,Ltd.ALL rights reserved.
# This program is licensed under Mulan PSL v2.
# You can use it according to the terms and conditions of the Mulan PSL v2.
#          http://license.coscl.org.cn/MulanPSL2
# THIS PROGRAM IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
####################################
# @Author  : Ethan-Zhang
# @email   : ethanzhang55@outlook.com
# @Date    : 2022/05/09 19:59:00
# @License : Mulan PSL v2
#####################################

FROM openeuler/openeuler:22.03-lts
LABEL maintainer="ethanzhang55@outlook.com"

ENV TZ Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENV GIT_REPO https://gitee.com/openeuler/radiaTest
ENV PIP_REPO https://pypi.tuna.tsinghua.edu.cn/simple
ENV BRANCH master

WORKDIR /opt

RUN dnf install -y git \
    && git clone -b $BRANCH $GIT_REPO \
    && dnf install -y make \
    && dnf install -y openssl \
    && dnf install -y expect \
    && dnf install -y iputils \
    && dnf install -y python3-pip \
    && dnf install -y python3-devel

WORKDIR /opt/radiaTest/radiaTest-server/

RUN bash ./install_rar.sh 
RUN pip3 install -r requirements.txt -i $PIP_REPO || pip3 install -r requirements.txt

CMD bash /opt/radiaTest/build/k8s-pod/web/gunicorn/init_db.sh \
    && bash /opt/radiaTest/build/k8s-pod/web/gunicorn/init_ca.sh\
    && gunicorn -c gunicorn/gunicorn.conf.py manage:app