import sys
import kom
import komparam


# MAIN

LIMIT = 12345

# Connect and log in

param = komparam.Parameters(sys.argv[1:])
(conn, conn_error) = param.connect_and_login(kom.CachedConnection)
if conn is None:
    sys.stderr.write("%s: %s\n" % (sys.argv[0], conn_error))
    sys.exit(1)

# Loop
no = 1
while no <= LIMIT:
    try:
        conf = conn.conferences[no]
        if conf.type.letterbox or conf.type.secret:
            no += 1
            continue
                
        print "%6d %6d %s" % (conf.nice, no, conf.name)
        
    except kom.UndefinedConference:
        pass

    no += 1
