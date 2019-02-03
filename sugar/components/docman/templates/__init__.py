# coding: utf-8
"""
Templates
"""
import os
import sugar.utils.files
from sugar.lib.logger.manager import get_logger


def get_template(name) -> str:
    """
    Get template by the name.

    :param name: the name of the template
    :return: Jinja2 template source
    """
    log = get_logger("template.get_template")
    tpl_path = os.path.join(os.path.dirname(__file__), "{}.jinja2".format(name))
    #log.debug("Get template '{}' for name '{}'", tpl_path, name)
    try:
        with sugar.utils.files.fopen(tpl_path, "r") as tpl_h:
            out = tpl_h.read()
    except Exception as exc:
        log.error("Failed getting template for '{}': {}", name, exc)

    return out
