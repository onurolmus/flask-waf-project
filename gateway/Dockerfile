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

ARG MODSECURITY_VERSION=v3.0.16
ARG NGINX_VERSION=1.30.3
ARG MODSECURITY_NGINX_VERSION=v1.0.4

RUN git clone \
        --depth 1 \
        --branch ${MODSECURITY_VERSION} \
        --recurse-submodules \
        https://github.com/owasp-modsecurity/ModSecurity.git \
        /usr/local/src/ModSecurity && \
    cd /usr/local/src/ModSecurity && \
    git submodule update --init --recursive && \
    ./build.sh && \
    ./configure && \
    make -j"$(nproc)" && \
make install && \
echo "/usr/local/modsecurity/lib" > /etc/ld.so.conf.d/modsecurity.conf && \
ldconfig
RUN git clone \
        --depth 1 \
        --branch ${MODSECURITY_NGINX_VERSION} \
        https://github.com/owasp-modsecurity/ModSecurity-nginx.git \
        /usr/local/src/ModSecurity-nginx && \
    curl -fsSL \
        https://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz \
        -o /tmp/nginx.tar.gz && \
    tar -xzf /tmp/nginx.tar.gz -C /usr/local/src && \
    mkdir -p \
        /etc/nginx \
        /usr/local/nginx/modules \
        /var/log/nginx && \
    cd /usr/local/src/nginx-${NGINX_VERSION} && \
    PKG_CONFIG_PATH=/usr/local/modsecurity/lib/pkgconfig \
    ./configure \
        --prefix=/usr/local/nginx \
        --sbin-path=/usr/local/sbin/nginx \
        --conf-path=/etc/nginx/nginx.conf \
        --modules-path=/usr/local/nginx/modules \
        --pid-path=/var/run/nginx.pid \
        --error-log-path=/var/log/nginx/error.log \
        --http-log-path=/var/log/nginx/access.log \
        --with-http_ssl_module \
        --with-http_v2_module \
        --with-http_realip_module \
        --with-threads \
        --with-compat \
        --with-cc-opt="-I/usr/local/modsecurity/include" \
        --with-ld-opt="-L/usr/local/modsecurity/lib -Wl,-rpath,/usr/local/modsecurity/lib" \
        --add-dynamic-module=/usr/local/src/ModSecurity-nginx && \
    make -j"$(nproc)" && \
    make install && \
    cp objs/ngx_http_modsecurity_module.so \
        /usr/local/nginx/modules/ && \
    rm -f /tmp/nginx.tar.gz
WORKDIR /opt/gateway

CMD ["sleep", "infinity"]