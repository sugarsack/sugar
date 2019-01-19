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
# Rule is that the third level should be a list
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
