import kom

# -- CONFIGURATION BEGINS HERE ---

# How to connect to the server
KOMSERVER = "192.168.1.12"
KOMPORT = 4894
KOMPERSON = 10
KOMPASSSWORD = ""

# File to log some information into
LOG_FILE = "/home/kent/lyskom/python-lyskom/maillog"

# File for message-id -> text-no database
# Note: the actual filename depends on what database shelve.py chooses.
ID_DB_FILE = "/home/kent/lyskom/python-lyskom/message-id"

# Text to prepend to subject header of appendices
APPENDIX_SUBJECT_PREFIX_NONAME = "Bilaga till: "
APPENDIX_SUBJECT_PREFIX = "Bilaga (%s) till: "

# Use comments or footnotes when linking appendices to the main article?
APPENDIX_COMMENT_TYPE = kom.MIC_COMMENT #or kom.MIC_FOOTNOTE

# Skip AI_MX_DATE (for use with buggy aux-items.conf:s)
SKIP_AI_MX_DATE = 0

# -- CONFIGURATION ENDS HERE ---
