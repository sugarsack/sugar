# Multiple task syntax.
# Rule: second level is always a list
#
# First way is to place a name of the target
# as an ID of the task
/etc/hosts:
  - system.io.file:
    - managed:
        - src: sugar://hosts
    - line:
        - remove: foo
        - add: bar
  - archive:
    - zip:

# Second way is to place name explicitly
# into a parameter. This help to use the same ID
# of the "batch task" over different targets
update_hosts:
  - system.io.file:
    - managed:
      - name: /etc/hosts
      - src: sugar://hosts
    - line:
      - name: /etc/ssh/ssh_config
      - remove: foo
      - add: bar
  - archive:
    - zip:
        - name: /etc/hosts

# Third way is to use positional
# arguments. In this case, first argument
# is always the name.
#
# Rule is that the third level should be a list
update_hosts_1:
  - file:
    - managed:
        - /etc/hosts
        - sugar://hosts

# Fourth way is like third way,
# except the only first parameter is positional
update_hosts_2:
  - file:
    - managed:
        - /etc/hosts
        - src: sugar://hosts

# Fifth way is like the other two above
# except the ID is the name by prefix "name:".
name:/etc/hosts:
  - file:
    - managed:
        - src: sugar://hosts

/etc/someconfig.conf:
  - file:
      - archived:
