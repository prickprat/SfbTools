import argparse
import logging
import logging.config
import logging_conf
import pyodbc



def main():
    args = parse_sys_args()
    mock_sql_queries(args.infile)

def extract_mock_config(infile_path):
    """
    Returns a dictionary of configuration settings.
    """
    with open(infile_path, mode="rt", errors="strict") as infile:
        with XMLMessageFactory(infile, SqlMockerMessage) as mock_gen:
            try:
                mock_msg = next(iter(mock_gen))
                return mock_msg.todict()
            except StopIteration as e:
                logging.error("StopIteration Error: Possibly an invalid " +
                              "or non-existent SqlMocker message.")
                raise ValueError("Invalid SqlMocker Message. Check the input file.")


def mock_sql_queries(infile_path):



def parse_sys_args():
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description="""
    Skype for Business SQL Mocker Tool.

    Mocks the Skype SQL Agent using pre-configured SQL queries.

    SQL Mock File Format:

        <SqlMocker>
            <Description>...</Description>
            <Configuration>
                <TargetUrl>...</TargetUrl>
                <MaxDelay>....</MaxDelay>
                <RealTime>....</RealTime>
            </Configuration>
        </SqlMocker>
        <LyncDiagnostic>
            ...
        </LyncDiagnostic>
        ...

    Configuration Options:
        Description -   Short description of the mock scenario. [Optional]
        """)
    arg_parser.add_argument("infile",
                            type=str,
                            help="""
                            Path to the input file.
                            This needs to be in the Mock file format as above.
                            """)
    return arg_parser.parse_args()


if __name__ == "__main__":
    # Load logging configurations
    logging.config.dictConfig(logging_conf.LOGGING_CONFIG)
    main()
