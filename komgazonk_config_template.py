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

# File to make a dump of the gazonk object to. Good to have for restorage
# if the program or LysKOM crashes.
DUMPFILE = "/FIXME/gazonkdump.p"
# Set to true if we should dump in binary format.
DUMPBIN = 0

# File to log some information into. Make sure the user executing
# komgazonk has write-permissions in the directory where this file
# resides.
LOGFILE = "/FIXME/log"
# Set to one if you want to log things in a file.
LOG = 0

# If you want to have a pid file, set to 1
PID = 1
# The location and name of the pid file
PIDFILE = "/FIXME/komgazonk.pid"

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

# When to display statistics.
# 0 - never
# 1 - hourly
# 2 - dayly
# 3 - weekly
# 4 - monthly
# 5 - yearly
GAZ_DISPLAY_STATISTICS = 4

# Sleephours. These hours no new clues and no new warnings are sent.
# I.e. it is like the clock doesn't go these hours.
GAZ_SLEEP_HOURS = [0, 1, 2, 3, 4, 5, 6]

# Max time sleeping during sleep hours (see MAX_SLEEP_TIME).
MAX_SLEEP_TIME_NIGHT = 600

# Set to 1 if correct guess should be showed in the end message of the round
GAZ_CORRECT_IN_END_MESSAGE = 1

# -- CONFIGURATION ENDS HERE ---
