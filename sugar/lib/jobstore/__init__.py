# coding: utf-8
"""
Job store.

This serves to manage jobs:

- Something was scheduled:
  - What scheduled (same as aftermath)
  - Who did that
  - When

- What is the status of it

- Aftermath analysis:
  - Contains log snippets of each task from each machine
  - Contains results of each task
  - Contains all other failures
"""

# flake8: noqa

from sugar.lib.jobstore.storage import JobStorage
