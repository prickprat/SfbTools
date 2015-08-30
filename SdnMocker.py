import mmap
from xml.etree.ElementTree import ParseError


class XMLMessageFactory:

    def __init__(self, file_obj, xml_wrapper):
        """
        root_regex  - re.compiled regex to find the root elements in the xml document.
        file_obj - input file object.
        xml_wrapper_cls   - the wrapper class that will process the parsed xml element.
        """
        self._root_rx = xml_wrapper.get_root_regex()
        self._file_obj = file_obj
        self._xml_wrapper = xml_wrapper

    def _open(self):
        self._mmap = mmap.mmap(self._file_obj.fileno(), 0, access=mmap.ACCESS_READ)

    def _close(self):
        self._mmap.close()

    def __del__(self):
        self._close()

    def __iter__(self):
        if self._mmap.closed:
            self._open()
        self._current_pos = 0
        self._mmap.seek(0)
        return self

    def __next__(self):
        if self._mmap.closed:
            raise StopIteration

        match = self._root_rx.search(self._mmap, self._current_pos)
        if match:
            try:
                self._current_pos = match.end()
                return self._xml_wrapper(match.group(0))
            except ParseError:
                print("Got a parse error. Stopping Iteration and closing file.")
                self._close()
                raise StopIteration
        else:
            raise StopIteration

    def __enter__(self):
        self._open()
        return self

    def __exit__(self, exec_type, exec_value, exec_tb):
        self.__del__()
        return False

