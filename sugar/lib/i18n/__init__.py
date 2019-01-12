# coding: utf-8
"""
i18n, based on Zope 2 ideas.
"""
from __future__ import absolute_import, unicode_literals
import os
import locale


class Gettext(object):
    """
    Get/add text
    """

    def __init__(self, domain="default", **conf):
        """
        Constructor.

        :param domain: domain of the messages. Default: "default".
        """
        self.path = os.path.join(os.path.dirname(__file__), "locales", locale.getlocale()[0], domain, "messages.yaml")
        self._plural_none = conf.get("none", 0)
        self.few = conf.get("few", 3)

    def load(self):
        """
        Load messages for the specific locale.

        :return: None
        """

    def gettext(self, text, count=0):
        """
        Get or add text.

        :param text: Text ID.
        :param count: count for plurals
        :return: translated text, if any
        """
        plural = "none"
        if count == 1:
            plural = "one"
        elif 1 < count <= self.few:
            plural = "few"
        elif count > self.few + 1:
            plural = "many"
        return self.__get(text, plural=plural)

    def __add(self, text, plural):
        """
        Adds a text to the messages and returns it back as is,
        because the text is new.
        One entry structure is following:
           {"sometext": ["sometranslation", {"many": "translations"}]}
           {"sometext": ["sometranslation, {}]}

        :param text: Text ID.
        :param plural: plurals section.
        :raises
        :return: None
        """

    def __get(self, text, plural):
        """
        Gets a text from the messages. If none found, adds one.
        One entry structure is following:
           {"sometext": ["sometranslation", {"many": "translations"}]}
           {"sometext": ["sometranslation, {}]}

        :param text: Text ID.
        :param plural: plurals section.
        :return: translated text.
        """
