# config: utf-8
"""
Docman unit tests.
"""
from mock import MagicMock, patch, mock_open
from sugar.components.docman.gendoc import DocMaker
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


class TestSuiteForDocman:
    """
    Test suite for the docman component.
    """
    #@patch("sugar.utils.files.fopen", multi_mock_open(sample_doc, sample_example, sample_scheme), create=True)
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
