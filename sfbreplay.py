from .replayer.replayer import SfbReplayer
import argparse
import logging
import logging.config
import logging_conf
import ast


def main():
    args = parse_sys_args()

    sdn_config = None
    odbc_config = None
    if args.sdn_config is not None:
        sdn_config = process_dict_arg(args.sdn_config)
    if args.odbc_config is not None:
        odbc_config = process_dict_arg(args.odbc_config)

    replayer = SfbReplayer.fromfile(args.infile,
                                    sdn_config=sdn_config,
                                    odbc_config=odbc_config)
    print(replayer)
    replayer.run()


def process_dict_arg(arg_str):
    """
    Converts a str representing a python dictionary to a dict.
    Raises ValueError if conversion is not possible.
    """
    try:
        dict_arg = ast.literal_eval(arg_str.strip())
        if not isinstance(dict_arg, dict):
            raise TypeError
        return dict_arg
    except (SyntaxError, TypeError, ValueError) as e:
        logging.error(str(e))
        raise ValueError("Invalid configuration argument.")


def parse_sys_args():
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description="""
    Skype for Business Mocker Tool.

    This tool is designed to replay a Conference or Call by sending pre-defined
    SDN messages directly to a receiver, and replaying predefined insert/delete
    statements against the SQL database.

    The tool requires a pre-defined 'Mocker Test' as an input file and configurations
    for the SDN receiver and ODBC connection as parameters.

    Each 'Mocker Test' is an XML document representing a test scenario.
    It contains test configurations and Mock Messages sent to either
    the SDN receiver or the database. Details below.

    --------------------------Mock Test File--------------------------

    *********** Format Example ****************

    <Mocker xmlns="http://www.ir.com/Mocker"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.ir.com/Mocker ../schemas/Mocker.Schema.xsd">

        <Description>...</Description>
        <MockerConfiguration>
            <MaxDelay>....</MaxDelay>
            <RealTime>....</RealTime>
            <CurrentTime>...</CurrentTime>
        </MockerConfiguration>
        <MockMessages>
            <LyncDiagnostic>
                ...
            </LyncDiagnostic>
            ...
            <SqlQueryMessage>
                <TimeStamp>...</TimeStamp>
                <Query><![CDATA[...]]></Query>
            </SqlQueryMessage>
            ...
        </MockMessages>
    </Mocker>

    *******************************************

    Elements explained :

        Mocker      -   The root element for the xml.
                        Namespace must be 'http://www.ir.com/Mocker' since this test is validated
                        against a schema before it is executed.
        Description -   Short description of the mock test scenario. [Optional]
        MaxDelay    -   The maximum delay time for each consecutive message.
                        Number of seconds.
                        (e.g. 120)
        RealTime    -   Realtime uses the actual time interval between consecutive
                        mock messages. The Max Delay time is still respected.
                        If disabled then the time delay is always Max Delay.
                        true or false.
                        (e.g. true)
        CurrentTime -   If CurrentTime is true, all timestamps for messages will be made relative
                        to the current date-time. The timestamp of the final MockMessage
                        will be replaced with the current UTC timestamp. Preceding message
                        timestamps will also be replaced, depending on RealTime and MaxDelay
                        settings.
                        true or false.
                        (e.g. true)

    -------------------SDN Configuration -----------------------------

    The SDN configuration must be in python dictionary format.

    The following SDN parameters are supported :
        receiver    -   Target URL for the http/https listener
        version     -   The SDN API version of the mock messages.
                        Optional. Default version is 2.1.1

        e.g. --sdn-config "{ 'receiver': 'https://127.0.0.1:3000/SdnApiReceiver/site',
                             'version' : '2.2' }"

    -------------------ODBC Configuration -----------------------------

    The ODBC connection parameters must be in python dictionary format.
    NB: Backslashes must be triple escaped (e.g. \\\\\\\\ for \\)

    The following ODBC parameters are supported :
        driver      -   Odbc Driver used for the connection.
        server      -   Location of database server.
        database    -   Database name. [Optional]
        uid         -   user id. [Optional]
        pwd         -   user password. [Optional]

        e.g. --odbc-config "{ 'driver': 'SQL SERVER',
                              'server': '10.102.70.4\\\\\\\\SqlServer',
                              'database': 'LcsCDR',
                              'uid': 'sa',
                              'pwd': 'C1sc0c1sc0' }" """)

    arg_parser.add_argument("infile",
                            type=str,
                            help="""
                            Path to the Mock Test XML file.
                            See the detailed description above for formatting.""")

    arg_parser.add_argument("--sdn-config",
                            metavar="SDN_PARAMS",
                            type=str,
                            help="""
                            SDN Mocker configuration parameters in python dictionary format.
                            See the detailed description above.""")

    arg_parser.add_argument("--odbc-config",
                            metavar="ODBC_PARAMS",
                            type=str,
                            help="""
                            ODBC connection string parameters in python dictionary format.
                            See the detailed description above.""")

    return arg_parser.parse_args()


if __name__ == "__main__":
    # Load logging configurations
    logging.config.dictConfig(logging_conf.LOGGING_CONFIG)
    main()
