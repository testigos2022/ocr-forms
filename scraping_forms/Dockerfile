FROM python:3.8.6-slim-buster as base_image
WORKDIR /root/scraping_forms

ENV APT_INSTALL="apt-get install -y --no-install-recommends"

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive $APT_INSTALL \
        build-essential \
        ca-certificates \
        curl \
        zip unzip \
        wget \
        git \
        g++ \
        cmake \
        vim \
        supervisor \
        python3-dev python3-pip python3-distutils && \
# ==================================================================
# clean up everything
# ------------------------------------------------------------------
    apt-get clean && \
    apt-get -y autoremove && \
    rm -rf /var/lib/apt/lists/*


RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    wget https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip -d /usr/bin
RUN chmod +x /usr/bin/chromedriver

# python venv
# python -m venv .venv
# source .venv/bin/activate
COPY scraping_forms /root/scraping_forms
RUN pip install -r requirements.txt

# DOCKER_BUILDKIT=1 docker build -t scraping_forms -f scraping_forms/Dockerfile .