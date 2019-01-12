# coding: utf-8
"""
i18n, based on Zope 2 ideas.
"""
from __future__ import absolute_import, unicode_literals
import os
import locale
import yaml
import sugar.utils.files
from sugar.lib.logger.manager import get_logger
from sugar.utils.objects import Singleton


@Singleton
class GetText(object):
    """
    Get/add text
    """

    def __init__(self):
        self.log = get_logger(self)
        for loc_val in [locale.getlocale()[0], "en_US"]:
            self.path = os.path.join(os.path.dirname(__file__), "locales", loc_val, "messages.yaml")
            if os.path.exists(self.path):
                break
            else:
                self.log.error("i18n messages file at {fname} is missing for locale {loc}.",
                               fname=self.path, loc=loc_val)
                self.path = None
        self._plural_none = 0
        self.few = 3
        self.__translations = {}
        self.load()

    def load(self) -> None:
        """
        Load messages for the specific locale.

        :return: None
        """
        if self.path is not None:
            with sugar.utils.files.fopen(self.path) as tr_fh:
                self.__translations = yaml.load(tr_fh.read()) or {}

    def save(self) -> None:
        """
        Save messages to the disk.
        Note: this won't do it on production, where packaged
              product is distributed read-only.

        :return: None
        """
        if self.path is not None:
            if os.access(self.path, os.W_OK):
                with sugar.utils.files.fopen(self.path, "w") as tr_fh:
                    tr_fh.write(yaml.dump(self.__translations, default_flow_style=False, allow_unicode=True))
            else:
                self.log.error("Unable to update i18n messages at {}", self.path)

    def gettext(self, text: str, count: int = 0) -> str:
        """
        Get a text translation or transparently add a new text (in development mode).

        :param text: Text ID.
        :param count: count for plurals
        :return: translated text, if any. Original, if nothing found.
        """
        plural = "none"
        if count == 1:
            plural = "one"
        elif 1 < count <= self.few:
            plural = "few"
        elif count > self.few:
            plural = "many"
        return self.__get(text, plural=plural)

    def __add(self, text: str, plural: str) -> str:
        """
        Adds a text to the messages and returns it back as is,
        because the text is new.

        One entry structure is following:
          {"sometext": {"many": "translations"}}
          {"sometext": {}}

        :param text: Text ID.
        :param plural: plurals section.
        :return: original text.
        """
        self.__translations.setdefault(text, {})
        self.__translations[text].setdefault(plural, text)
        self.save()

        return text

    def __get(self, text: str, plural: str) -> str:
        """
        Gets a text from the messages. If none found, adds one.
        One entry structure is following:
           {"sometext": {"many": "translations"}}
           {"sometext": {}}

        :param text: Text ID.
        :param plural: plurals section.
        :return: translated text.
        """
        translation = self.__translations.get(text, {})
        if translation:
            tr_text = translation.get(plural)
            if not tr_text:
                tr_text = self.__add(text, plural=plural)
        else:
            tr_text = self.__add(text, plural=plural)

        return tr_text


def gettext(text, count=0):
    """
    Usable gettext.

    :param text: Text for translation
    :param count: count for plurals
    :return: Translated text
    """
    return GetText().gettext(text=text, count=count)
