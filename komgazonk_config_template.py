import kom

# -- CONFIGURATION BEGINS HERE ---

# How to connect to the server. 
KOMSERVER = "FIXME"     # Name or IP address
KOMPORT = 4894		    # Port number

# The LysKOM person that's that should send and recieve messages and
# letters.
KOMPERSON = FIXME           # LysKOM person number
KOMPASSWORD = "FIXME"      # Password of KOMPERSON

# The conference to send letters to, with clues and such things.
GAZONK_CONF = FIXME

# File to log some information into. Make sure the user executing
# komgazonk has write-permissions in the directory where this file
# resides.
LOGFILE = "/FIXME/maillog"
# Set to one if you want to log things in a file.
LOG = 0

# Max time gazonk should take between checking if we should out
# another letter (in seconds).
MAX_SLEEP_TIME = 60
# Time between clues (in seconds).
GAZONK_CLUE_TIME = 86400 # (24 hours)
# Time between each reminder (in seconds).
GAZONK_REMEMBER_TIME = 86400 # (24 hours)
# Allowed characters in the password.
GAZ_PW_CHARS = "a-zедц"
# Max length of the password
GAZ_PW_LENGTH = 12
# Number of warnings before gazonk is thrown out.
GAZ_MAX_WARNINGS = 4

# -- CONFIGURATION ENDS HERE ---
