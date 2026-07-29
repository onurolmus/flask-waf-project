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
ARG CRS_VERSION=4.28.0

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

    RUN mkdir -p /etc/nginx/modsecurity && \
    cp /usr/local/src/ModSecurity/modsecurity.conf-recommended \
       /etc/nginx/modsecurity/modsecurity.conf && \
    cp /usr/local/src/ModSecurity/unicode.mapping \
       /etc/nginx/modsecurity/unicode.mapping && \
    sed -i \
        's|SecRuleEngine DetectionOnly|SecRuleEngine On|' \
        /etc/nginx/modsecurity/modsecurity.conf && \
    sed -i \
        's|SecUnicodeMapFile unicode.mapping 20127|SecUnicodeMapFile /etc/nginx/modsecurity/unicode.mapping 20127|' \
        /etc/nginx/modsecurity/modsecurity.conf

        RUN git clone \
        --depth 1 \
        --branch v${CRS_VERSION} \
        https://github.com/coreruleset/coreruleset.git \
        /etc/nginx/modsecurity/crs && \
    cp /etc/nginx/modsecurity/crs/crs-setup.conf.example \
       /etc/nginx/modsecurity/crs/crs-setup.conf && \
    test -f /etc/nginx/modsecurity/crs/crs-setup.conf && \
    rm -rf /etc/nginx/modsecurity/crs/.git

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY modsecurity/main.conf /etc/nginx/modsecurity/main.conf
RUN mkdir -p /etc/nginx/tls

COPY tls/server.crt /etc/nginx/tls/server.crt
COPY tls/server.key /etc/nginx/tls/server.key

RUN chmod 600 /etc/nginx/tls/server.key

EXPOSE 443

WORKDIR /opt/gateway

CMD ["/usr/local/sbin/nginx", "-g", "daemon off;"]