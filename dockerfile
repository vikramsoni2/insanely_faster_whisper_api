FROM nvidia/cuda:12.1.0-devel-ubuntu20.04
 
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV API_PORT 8080
ENV HF_HUB_CACHE=/api/models
ENV HF_HOME=/api/models
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    software-properties-common

# Add deadsnakes PPA for Python 3.10
RUN add-apt-repository ppa:deadsnakes/ppa

# Update package lists again
RUN apt-get update

# Install Python 3.10 and its development headers
RUN apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-distutils

# Install pip for Python 3.10
RUN apt-get install -y \
    python3.10-distutils \
    curl
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3.10 get-pip.py

# Clean up unnecessary files
RUN rm get-pip.py
 
WORKDIR /api
 
RUN apt-get install -y ffmpeg\
&& apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
&& mkdir /api/models/
 
COPY ./requirements.txt .
RUN pip install -r requirements.txt
EXPOSE 8000

COPY ./ .
RUN chmod +x /api/entrypoint.sh
 
ENTRYPOINT ["/api/entrypoint.sh"]
