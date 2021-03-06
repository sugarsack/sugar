# config: utf-8
"""
Docman unit tests.
"""
import os
import pytest

from mock import MagicMock, patch, mock_open
from sugar.components.docman.gendoc import DocMaker, ModCLIDoc
import sugar.lib.exceptions
from tests.unit.unit_utils import multi_mock_open


def get_fake_loader():
    """
    Construct a fake loader for mocking.

    :return:
    """
    loader = MagicMock()
    loader.runners = MagicMock()
    loader.runners.root_path = "/dev/null/runners"
    loader.states = MagicMock()
    loader.states.root_path = "/dev/null/states"
    loader_class = MagicMock(return_value=loader)

    return loader_class


sample_doc = """
module:
  name: name
  author: Luke Skywalker <luke@walker.sky>
  summary: Greeter
  synopsis: |
    This module greets
  since_version: 0.0.1

tasks:
  hello:
    description:
      - This mode dealing with ether leaks
      - and short legs on process table
    parameters:
      name:
        description:
          - Some random parameter
        required: false
        default: "Yoda"
        type: str
"""

sample_example = """
hello:
  description:
    - Data about this example.
    - Each item in this list is a sentence in the documentation.

  commandline: |
    sugar \* foo

  states: |
    some_id:
      foo:
        - hello:
"""

sample_scheme = """
NameInterface:
  platform:
    r:name: str
"""


class TestSuiteForModCLIDocClass:
    """
    Test suite for the docman component on module CLI documentation class.
    """
    def test_filters(self):
        """
        Check filters instance.

        :return:
        """
        assert ModCLIDoc.filters.__class__.__name__ == "JinjaCLIFilters"

    def test_mtype_or_mpath_expected(self):
        """
        Check m_type or m_path has been specified (either).

        :return:
        """
        with pytest.raises(AssertionError) as exc:
            ModCLIDoc("foo.bar")
        assert "Either module type or path should be specified" in str(exc)

    def test_no_documentation_found(self):
        """
        No documentation found should raise AssertionError.

        :return:
        """
        with pytest.raises(sugar.lib.exceptions.SugarException) as exc:
            ModCLIDoc("foo.bar", mod_type="runner", mod_path="/tmp")
        assert "No documentation found for runner module 'foo.bar'" in str(exc)

    @patch("sugar.utils.files.fopen", multi_mock_open(sample_doc, sample_example, sample_scheme,
                                                      sample_doc, sample_example, sample_scheme), create=True)
    def test_mcd_docmap(self):
        """
        Test documentation mapper.

        :return:
        """
        for mod_type in ["runner", "state"]:
            mcd = ModCLIDoc("foo.bar", mod_type=mod_type)
            assert len(mcd._docmap) == 3

            for pkey in ["doc", "examples", "scheme"]:
                assert pkey in mcd._docmap

            assert bool(mcd._mod_path)
            assert mcd._mod_path.startswith(os.path.sep)
            assert mcd._mod_path.endswith("/sugar/modules/{}s/foo/bar".format(mod_type))

    @patch("sugar.utils.files.fopen", multi_mock_open(sample_doc, sample_example, sample_scheme), create=True)
    @patch("sugar.components.docman.docrnd.yaml.load", MagicMock(side_effect=[
        {"doc": "documentation"}, IOError("Static from nylon underwear"), {"sch": "scheme"}]))
    def test_docmap_resistance(self):
        """
        When constructing a docmap and a specific doc is missing,
        it should still create a section with an empty dict.

        :return:
        """
        mcd = ModCLIDoc("foo.bar", mod_type="runner")
        for pkey in ["doc", "examples", "scheme"]:
            assert pkey in mcd._docmap

        assert mcd._docmap["examples"] == {}
        assert mcd._docmap["doc"]["doc"] == "documentation"
        assert mcd._docmap["scheme"]["sch"] == "scheme"

    def test_add_ident(self):
        """
        Add ident to the multi-line text.

        :return:
        """
        data = "one\ntwo\ntree"
        data = ModCLIDoc._add_ident(data=data, ident="...")

        assert "...one\n...two\n...tree" == data

    @patch("sugar.utils.files.fopen", multi_mock_open(sample_doc, sample_example, sample_scheme), create=True)
    def test_object_example(self):
        """
        Get object examples.

        :return:
        """
        mcd = ModCLIDoc("foo.bar", mod_type="runner")
        examples = mcd.get_object_examples("hello")
        assert len(examples) == 3
        assert examples[0].startswith("Data about this example.")
        assert examples[1].startswith("\x1b[38;5;10m")
        assert examples[1].endswith("\x1b[0m")


class TestSuiteForDocman:
    """
    Test suite for the docman component.
    """
    @patch("sugar.components.docman.docrnd.SugarModuleLoader", get_fake_loader())
    def test_docmaker_runner_get_mod_man(self):
        """
        Test get_mod_man function of the DocMaker on runner.

        :return:
        """
        mod_type = "runner"
        mod_cli_doc = MagicMock()
        loader = get_fake_loader()
        with patch("sugar.components.docman.gendoc.SugarModuleLoader", loader) as sml, \
            patch("sugar.components.docman.gendoc.ModCLIDoc", mod_cli_doc) as mcd:
            dmk = DocMaker()
            dmk.get_mod_man(mod_type, "foo.bar")

        params = list(mod_cli_doc.call_args_list[0])
        assert len(params) == 2
        assert params[0][0] == 'foo.bar'
        for pkey in ["mod_path", "mod_type"]:
            assert pkey in params[1]
        assert params[1]["mod_type"] == mod_type
        assert params[1]["mod_path"] == "/dev/null/runners/foo/bar"

    @patch("sugar.components.docman.docrnd.SugarModuleLoader", get_fake_loader())
    def test_docmaker_state_get_mod_man(self):
        """
        Test get_mod_man function of the DocMaker on state.

        :return:
        """
        mod_type = "state"
        mod_cli_doc = MagicMock()
        loader = get_fake_loader()
        with patch("sugar.components.docman.gendoc.SugarModuleLoader", loader) as sml, \
            patch("sugar.components.docman.gendoc.ModCLIDoc", mod_cli_doc) as mcd:
            dmk = DocMaker()
            dmk.get_mod_man(mod_type, "foo.bar")

        params = list(mod_cli_doc.call_args_list[0])
        assert len(params) == 2
        assert params[0][0] == 'foo.bar'
        for pkey in ["mod_path", "mod_type"]:
            assert pkey in params[1]
        assert params[1]["mod_type"] == mod_type
        assert params[1]["mod_path"] == "/dev/null/states/foo/bar"

    @patch("sugar.components.docman.docrnd.SugarModuleLoader", get_fake_loader())
    @patch("sugar.components.docman.gendoc.ModCLIDoc", MagicMock())
    def test_dockmaker_get_mod_man_other(self):
        """
        Test get_mod_man raises and exception if documentation is not for runners or state modules.

        :return:
        """
        mod_type = "custom"
        loader = get_fake_loader()
        with patch("sugar.components.docman.gendoc.SugarModuleLoader", loader):
            dmk = DocMaker()
            with pytest.raises(sugar.lib.exceptions.SugarException) as exc:
                dmk.get_mod_man(mod_type, "foo.bar")
            assert "Custom modules documentation is not supported yet." in str(exc)

    def test_dockmaker_get_func_man_other(self):
        """
        Test get_func_man returns nothing if not runner or state mod type.

        :return:
        """
        mod_type = "custom"
        loader = get_fake_loader()
        with patch("sugar.components.docman.gendoc.SugarModuleLoader", loader):
            dmk = DocMaker()
            assert not bool(dmk.get_func_man(mod_type, "foo.bar"))

    @patch("sugar.components.docman.gendoc.SugarModuleLoader", get_fake_loader())
    def test_dockmaker_get_func_man_runner(self):
        """
        Test get_func_man returns nothing if not runner or state mod type.

        :return:
        """
        mod_type = "runner"
        mod_cli_doc = MagicMock()
        with patch("sugar.components.docman.gendoc.ModCLIDoc", mod_cli_doc):
            dmk = DocMaker()
            dmk.get_func_man(mod_type, "foo.bar")
        params = list(mod_cli_doc.call_args_list[0])
        assert len(params) == 2
        assert params[0][0] == "foo"
        for pkey in ["functions", "mod_type", "mod_path"]:
            assert pkey in params[1]
        assert params[1]["functions"] == ["bar"]
        assert params[1]["mod_path"] == "/dev/null/runners/foo"
        assert params[1]["mod_type"] == mod_type

    @patch("sugar.components.docman.gendoc.SugarModuleLoader", get_fake_loader())
    def test_dockmaker_get_func_man_state(self):
        """
        Test get_func_man returns nothing if not state or state mod type.

        :return:
        """
        mod_type = "state"
        mod_cli_doc = MagicMock()
        with patch("sugar.components.docman.gendoc.ModCLIDoc", mod_cli_doc):
            dmk = DocMaker()
            dmk.get_func_man(mod_type, "foo.bar")
        params = list(mod_cli_doc.call_args_list[0])
        assert len(params) == 2
        assert params[0][0] == "foo"
        for pkey in ["functions", "mod_type", "mod_path"]:
            assert pkey in params[1]
        assert params[1]["functions"] == ["bar"]
        assert params[1]["mod_path"] == "/dev/null/states/foo"
        assert params[1]["mod_type"] == mod_type
