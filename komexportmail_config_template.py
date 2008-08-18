# -- CONFIGURATION BEGINS HERE ---

# How to connect to the server. 
KOMSERVER = "FIXME"             # Name or IP address
KOMPORT = 4894		        # Port number

# The LysKOM person that exports messages.
KOMPERSON = FIXME               # LysKOM person number
KOMPASSWORD = "FIXME"           # Password of KOMPERSON

# How to deliver the exported messages. The domain should preferably be
# one that is used for importing mail to this KOM system.
MAILSERVER = "FIXME"            # Name or IP address
MAILDOMAIN = "FIXME"            # Domain of the sender

# Where to store the settings database.
DATABASE = "/FIXME/exportdb"

# Where to write the log.
LOGFILE = "/FIXME/exportlog"

# Language setting ("en" for English or "sv" for Swedish).
LANGUAGE = "sv"

# If a LysKOM text lacks a content-type aux-item, assume this character
# encoding. You probably don't want to change this unless you know what
# you are doing. ISO 8859-1 is the default for LysKOM servers.
DEFAULT_CHARSET = "iso-8859-1"

# String to identify this software.
SOFTWARE_ID = "komexportmail"

# The LysKOM persons who get emergency notifications and can send admin
# commands. If you don't plan on working with the code, you may want to
# leave this empty. Otherwise, use person numbers (e.g. "[5, 6]").
ADMINS = []

# -- CONFIGURATION ENDS HERE ---
