FROM alpine:3.7

ENV PYTHONUNBUFFERED 1

RUN apk update && \
    apk upgrade && \
    apk add --no-cache \
      gcc g++ paxctl libgcc libstdc++ make cmake musl-dev libffi-dev openssl-dev linux-headers libxml2-dev libxslt-dev python python-dev python3 python3-dev libc-dev libunwind-dev alpine-sdk xz poppler-dev pango-dev m4 libtool perl autoconf automake coreutils zlib-dev freetype-dev glib-dev libpng freetype libintl libltdl cairo

# This next RUN is from https://github.com/BWITS/Docker-builder/blob/master/pdf2htmlEX/alpine/Dockerfile
# Used here with 3.7 because of libunwind-dev, which is not available on alpine 3.2's package index
RUN cd / && \
    git clone https://github.com/BWITS/fontforge.git && \
    cd fontforge && \
    ./bootstrap --force && \
    ./configure --without-iconv && \
    make && \
    make install && \
    cd / && \
    git clone git://github.com/coolwanglu/pdf2htmlEX.git && \
    cd pdf2htmlEX && \
    export PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/local/lib/pkgconfig && \
    cmake . && make && sudo make install && \
    rm -rf /fontforge /libspiro /libuninameslist /pdf2htmlEX

RUN mkdir /code
WORKDIR /code

COPY ./requirements.txt /requirements.txt
COPY ./entrypoint.sh /code/entrypoint.sh
COPY ./cv-parser /cv-parser

RUN pip3 install --upgrade setuptools && pip3 install --upgrade pip
RUN pip3 install -r /requirements.txt

ENTRYPOINT ["/bin/sh", "entrypoint.sh"]
