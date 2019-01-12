# coding: utf-8
"""
i18n, based on Zope 2 ideas.
"""
from __future__ import absolute_import, unicode_literals
import os
import yaml
import locale
import sugar.utils.files
from sugar.lib.logger.manager import get_logger


class GetText(object):
    """
    Get/add text
    """

    def __init__(self, domain="default", **conf):
        """
        Constructor.

        :param domain: domain of the messages. Default: "default".
        """
        self.log = get_logger(self)
        for loc_val in [locale.getlocale()[0], "en_US"]:
            self.path = os.path.join(os.path.dirname(__file__), "locales", loc_val, domain, "messages.yaml")
            if os.path.exists(self.path):
                break
            else:
                self.path = None
                self.log.error("i18n messages file at {fname} is missing for locale {loc}.",
                               fname=self.path, loc=loc_val)
        self._plural_none = conf.get("none", 0)
        self.few = conf.get("few", 3)
        self.load()
        self.__translations = {}

    def load(self):
        """
        Load messages for the specific locale.

        :return: None
        """
        if self.path is not None:
            with sugar.utils.files.fopen(self.path) as tr_fh:
                self.__translations = yaml.load(tr_fh.read())

    def save(self):
        """
        Save messages.

        :return: None
        """
        if self.path is not None:
            with sugar.utils.files.fopen(self.path, "w") as tr_fh:
                tr_fh.write(yaml.dump(self.__translations, default_flow_style=False))

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
        self.__translations.setdefault(text, [text, {plural: text}])  # Add the same text for further edit
        return text

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
        tr_text, plurals = self.__translations.get(text, (None, None))
        if tr_text is not None:
            tr_text = plural.get(plural, tr_text)
        else:
            tr_text = self.__add(text, plural=plural)

        return tr_text
