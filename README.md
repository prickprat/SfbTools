# Skype for Business Tools


TODO

configuration on commandline string

--sdn-config="..."
--odbc-config="..."


mocker configuration :
    maxdelay
    realtime

Mocker is OPTIMISTIC : each message is performed in isolation :-> catches errors and moves on to next. prevents dirty tests. e.g. if sdn mocker not configured but sql is.

CLEANUP needs to be done within each Test

NEED mongodb or something for testing pyodbc side of mocking !!! 


EDGE CAse testing

message with no mocker configuration
JSON not a dictionary ??



