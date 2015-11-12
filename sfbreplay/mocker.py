import logging
import http.client
from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
import time
import pyodbc
import abc


class MockerInterface(metaclass=abc.ABCMeta):

    """
    Interface for Mockers
    """

    def __init__(self, **config_dict):
        self._closed = True

    @classmethod
    def fromdict(cls, config_dict):
        """
        Initialize the Mocker from dictionary.
        """
        return cls(**config_dict)

    @abc.abstractmethod
    def __str__(self):
        """Prints a readable representation of the Mocker and Configurations"""

    @abc.abstractmethod
    def open(self, data):
        """Stages the Mocker for sending data to the end point."""

    @abc.abstractmethod
    def close(self, data):
        """Releases any resources held by an open Mocker."""

    @abc.abstractmethod
    def send(self, data):
        """Sends the data to the configured end point. Mocker must be open."""

    def send_message(self, msg, delay):
        """
        Sends the given Message to the configured endpoint using the mocker send method.
        The delay is applied before the message is sent.

        msg     -   an instance of xmlmessage
        delay   -   number of seconds to delay the send request.
        """
        try:
            print('{0} Sleeping for {1}s.'.format(self.__class__.__name__, delay))
            time.sleep(delay)
            print("Sending : " + str(msg))
            if self.send(msg.tostring(encoding="us-ascii").encode("us-ascii")):
                print("Message sent successfully.")
        except URLError as e:
            logging.error("URLError : " + str(e))
            print("Connection Error! Check the End point in the Mocker configuration.")


class SdnMocker(MockerInterface):

    """
    Generates a configurable instance of a SDN mocker.
    Uses the Mocker interface.
    """

    def __init__(self, **kwargs):
        try:
            self.receiver = kwargs['receiver']
            self.version = kwargs['version']
            super().__init__(**kwargs)
        except KeyError as e:
            logging.error("KeyError : " + str(e))
            raise ValueError("receiver and version must be given as a keyword parameter.")

    def open(self):
        """
        Returns true if the receiver is responsive to POST requests.
        """
        if self._closed:
            try:
                response = urlopen(self.receiver, data="".encode("us-ascii"), timeout=1)
                if response.status == http.client.OK:
                    self._closed = False
                    return True
            except URLError:
                print("Failed to Open Connection!")
                return False
        else:
            return True

    def close(self):
        """
        Closes the Sdn Mocker Connection.
        """
        self._closed = True
        return True

    def send(self, data):
        """
        Sends a http POST request to the configured Target Url.
        Raises URLError on errors.

        Returns True if client received a
        response from the server, False otherwise.

        data    -   String in byte code format (e.g. us-ascii or utf-8 encoded)
        """
        if self._closed:
            print("Sdn Mocker is closed. Ignoring send request.")
            return False

        post_request = Request(self.receiver,
                               data=data,
                               headers={'Content-Type': 'application/xml'})
        response = urlopen(post_request)

        return True if response is not None else False

    def __str__(self):
        return "SdnMocker ::: receiver - {0} : version - {1}".format(self.receiver, self.version)


class OdbcMocker(MockerInterface):

    """
    Generates a configurable instance of an ODBC mocker.
    Uses the Mocker interface.
    """

    def __init__(self, **kwargs):
        try:
            self.driver = kwargs['driver']
            self.server = kwargs.get('server')
            self.database = kwargs['database']
            self.uid = kwargs['uid']
            self.pwd = kwargs['pwd']
            self._connection = None
            super().__init__(**kwargs)
        except KeyError as e:
            logging.error("KeyError : " + str(e))
            raise ValueError(
                "driver, server, database, uid, pwd must be given as keyword parameters.")

    def open(self):
        """
        Opens the odbc connection.
        """
        try:
            if self._closed:
                self._connection = pyodbc.connect(driver=self.driver,
                                                  server=self.server,
                                                  database=self.database,
                                                  uid=self.uid,
                                                  pwd=self.pwd)
                self._closed = False
        except:
            print("POKEMON EXCEPTION!!")
            raise

    def close(self):
        """
        Closes the odbc connection.
        """
        if not self._closed and self._connection is not None:
            self._connection.close()
        self._closed = True

    def send(self, data):
        """
        Executes and Commits the given query using an existing connection.
        """
        if self._closed:
            logging.debug("Connection is Closed. Ignoring Send Command.")
            return

        cursor = self._connection.cursor()
        cursor.execute(data)
        self._connection.commit()

    def send_message(self, sql_msg, delay):
        """
        """
        print('Odbc Mocker Sleeping for {0}s.'.format(delay))
        time.sleep(delay)
        print("Sending Sql Query Message : " + str(sql_msg))
        self.send(sql_msg.get_query())

    def __str__(self):
        template = "ODBC Mocker ::: driver - {0} : server - {1} : " + \
            " database - {2} : uid - {3} : pwd- {4}"
        return template.format(self.driver, self.server, self.database, self.uid, self.pwd)
