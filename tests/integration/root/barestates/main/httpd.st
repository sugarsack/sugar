import:
  - services.ssl
  - services.ssh

httpd_installed:
  pkg.installed:
    name: apache
