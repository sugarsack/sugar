job:install_stuff:
  webstack:
    pkg.installed:
      - pkgs:
          - httpd
          - postgresql
          - python
  /etc/hosts:
    file.line:
      - replace:
          from: web 127.0.0.1
          to: web 192.168.0.5

job:examine:
  info_installed:
    pkg.list_packages:
  get_traits:
    traits.get:
      - os_family
