# coding: utf-8
"""
Object render library.

Since in theory every substate can be written in a different way,
at the end it should return just a YAML structure.
"""
import os
from abc import ABCMeta, abstractmethod
import jinja2
import sugar.lib.exceptions


class BaseRenderer(metaclass=ABCMeta):
    """
    Basic renderer.
    """
    __shebang__ = "#!yaml"

    def __init__(self, **namespace):
        """
        Constructor and namespaces.
        """
        self.__namespace = namespace

    @property
    def namespace(self):
        """
        Namespace of the Sugar exported functions to the states.

        :return: namespace dictionary
        """
        return self.__namespace

    @abstractmethod
    def render(self, data):
        """
        Render the data.

        :param data: data to process
        :return: YAML
        """


class Jinja2Renderer(BaseRenderer):
    """
    Jinja2 renderer.
    """
    def render(self, data):
        """
        Render the Jinja2 template

        :param data: data to process
        :return: YAML
        """
        return jinja2.Template(data).render(**self.namespace)


__renderer_registry = {
    Jinja2Renderer.__shebang__: Jinja2Renderer
}


def render(src):
    """
    Render the substate source.

    :param src: substate.
    :return: Rendered YAML
    """
    shebang = src.split(os.linesep)[0]
    if not shebang.startswith("#!"):
        shebang = BaseRenderer.__shebang__
    renderer = __renderer_registry.get(shebang)
    if renderer is None:
        sugar.lib.exceptions.SugarSCException("Unable to render state: unknown shebang '{}'.".format(shebang))

    # Put the namespace here
    return renderer().render(src)
