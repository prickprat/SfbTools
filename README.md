# Skype for Business Tools v1.0.0


TODO

EDGE Case testing
    SQL SERVER connection error handling.

    cxn = pyodbc.connect("DRIVER={SQLite3 ODBC Driver};SERVER=localhost;DATABASE=C:/Users/prickprat/Documents/Programming/SqliteDatabases/test.db;Trusted_connection=yes")

Better Logging:
    Error Logging
    Debug logging
    Print statements
        sdn message printing
        configuration printing



System Testing
    * full test on sqlite & node server
    * 

Better handling of removing default namespaces:
    * REMOVE target ns from schema?
    * DONT use re replace
    * 

PRIORITY:

sdn version in SdnMocker
remove default namespaces in sdn message printing
If no timestamp found default to 0 interval , log warning.
duplicate xmlmessage in sdnextractor
