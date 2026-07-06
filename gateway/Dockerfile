FROM rockylinux:8

RUN dnf -y update && \
    dnf -y install dnf-plugins-core && \
    dnf config-manager --set-enabled powertools && \
    dnf -y install \
        gcc \
        gcc-c++ \
        make \
        autoconf \
        automake \
        libtool \
        bison \
        flex \
        git \
        curl \
        curl-devel \
        wget \
        ca-certificates \
        pcre2-devel \
        zlib-devel \
        openssl-devel \
        libxml2-devel \
        yajl-devel \
        pkgconf-pkg-config \
        tar \
        gzip \
        which && \
    dnf clean all

WORKDIR /opt/gateway

CMD ["sleep", "infinity"]