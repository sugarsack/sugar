# Four ways of writing the same single task
# Rule: second level is always a key.
#
# First way is to place a name of the target
# as an ID of the task
/etc/hosts:
  file.managed:
    - src: sugar://hosts

# Second way is to place name explicitly
# into a parameter
update_hosts:
  file.managed:
    - name: /etc/hosts
    - src: sugar://hosts

# Third way is to use positional
# arguments. In this case, first argument
# is always the name.
#
# Rules:
#  - is that the third level should be a list
#  - if there is no prefix "name:" in the ID,
#    then the first element is the name.

update_hosts_1:
  file.managed:
    - /etc/hosts
    - sugar://hosts

# Fourth way is like third way,
# except the only first parameter is positional
update_hosts_2:
  file.managed:
    - /etc/hosts
    - src: sugar://hosts

# Fifth way is to point out that the ID is the name
# by adding a prefix. Modules can have own namespace!
name:/etc/hosts:
  system.io.file.managed:
    - sugar://hosts
    - user: root
