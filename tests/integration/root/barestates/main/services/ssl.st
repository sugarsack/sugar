pyssl:
  pkg:
    - installed:
        name: python3-openssl
  file:
    - managed:
        name: /etc/ssl.conf
        src: sugar://ssl.conf
