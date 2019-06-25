# coding: utf-8
"""
State collector is to incrementally collect state source tree.
The state might be one file, or might include resources. This
must be compiled on the client side and make sure that the
conditions are met. For example, conditions might or might not
include more resources, which are still are not on the client.
This approach allows to compile till some degree and request
for further part from the server.

The downside of this approach that the state is compiled multiple
times unless it finally resolves all the pieces. However, client
is transferring only what is needed for the particular task,
instead of copying the entire library of formulas, available on
the server.
"""
import os
import shutil
import typing

from sugar.lib.logger.manager import get_logger
from sugar.lib.compiler import StateCompiler
import sugar.utils.files
from sugar.lib.compat import yaml
import sugar.lib.exceptions


class StateCollector:
    """
    State collector will create a path of /DEFAULT_ROOT/JID for
    each state job and then there will assemble the further
    pieces, concurrently.
    """
    DEFAULT_ROOT = "/var/cache/sugar/client/states"
    METADATA = ".meta"

    def __init__(self, jid: str, uri: str = None, env: str = None, root: str = None):
        """
        Constructor.

        :param jid: Job ID to resolve the state place.
        :param uri: URI of the state. If URI is not provided, then the job considered new.
        :param env: environment, used by the state. Otherwise default (main) is used.
        :param root: alternative state collector root, otherwise default is used.
        """
        self._base_root = root or self.DEFAULT_ROOT
        self._jid = jid
        self.log = get_logger(self)
        self.__compiled_data = None

        if uri:
            self.meta = {
                "uri": uri,
                "env": env or "main",
            }
            if not os.path.exists(self.state_root()):
                os.makedirs(self.state_root(), exist_ok=True)

            with sugar.utils.files.fopen(os.path.join(self.state_root(), self.METADATA), "w") as meta_fh:
                yaml.dump(self.meta, meta_fh)
        else:
            self.meta = self.get_meta()

    def get_meta(self) -> dict:
        """
        Get state metadata.

        :return: metadata
        """
        with sugar.utils.files.fopen(os.path.join(self.state_root(), self.METADATA), "r") as meta_fh:
            return yaml.load(meta_fh)

    def next_hop(self) -> str:
        """
        Tried to compile the source and see if there is another hop
        for the unresolved source. As long as no more hops are found,
        None is returned and the state source tree considered finished.
        Otherwise uri is returned for the next hop.

        :return: uri string for the next hop or None
        """
        container = {}

        def collect(path, uri):
            """
            Collect path and uri on URI exception.

            :param path:
            :param uri:
            :return:
            """
            container["path"] = path
            container["uri"] = uri

        meta = self.get_meta()
        compiler = StateCompiler(root=self.state_root(),
                                 environment=meta.get("env")).add_callback(collect, section="uri_error")
        try:
            compiler.compile(meta.get("uri"))
            self.__compiled_data = compiler.tasklist
            self._assign_jid()
        except sugar.lib.exceptions.SugarSCResolverException as ex:
            self.log.debug("Request for URI: {}", container.get("uri"))

        return container.get("uri")

    def _assign_jid(self):
        """
        Assigns current JID to each task.
        This method is called after successful state compilation.

        :return:
        """
        for task in self.tasks:
            for fn_call in task.calls:
                fn_call.jid = self._jid

    @property
    def tasks(self) -> typing.Tuple:
        """
        Return compiled tasks.

        :return:
        """
        return self.__compiled_data

    def state_root(self) -> str:
        """
        Returns state root of BASE_ROOT/JID.

        :return: path of the state root.
        """
        return os.path.join(self._base_root, self._jid)

    def add_resource(self, relative_path: str, source: str) -> None:
        """
        Add resource that is placed to the root path following relative path.

        :param relative_path: relative full path for the resource.
        :param source: Source of the file
        :return: None
        """
        assert bool(source), "Source required"
        assert bool(relative_path), "Relative path is not specified"

        if relative_path.startswith(os.path.sep):
            relative_path = relative_path.strip(os.path.sep)

        filename = os.path.basename(relative_path)
        dirname = os.path.dirname(relative_path)
        fpath = os.path.join(self.state_root(), self.meta["env"], dirname, filename)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with sugar.utils.files.fopen(fpath, "w") as resfh:
            resfh.write(source.strip() + os.linesep)

    def cleanup(self) -> None:
        """
        Cleanup the data after job is finished.

        :return: None
        """
        try:
            shutil.rmtree(self.state_root())
        except Exception as exc:
            self.log.error("Error removing state root for {}: {}", self._jid, self.state_root())
