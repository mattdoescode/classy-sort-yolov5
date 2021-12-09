import psycopg2
from config import config

# this script gets the information from postgres about both cameras
# it them combines the data and makes a 3d map that follows the fish
# this script is also the VR screen for the fish

# """ Connect to the PostgreSQL database server """

conn = None
try:
    # read connection parameters
    params = config()

    # connect to the PostgreSQL server
    print('Connecting to the PostgreSQL database...')
    conn = psycopg2.connect(**params)
    conn.autocommit = True

    # create a cursor
    cur = conn.cursor()

    # get 2 most recent tables created
    query = \
    """
        (SELECT table_name FROM information_schema.tables
                      WHERE table_schema='public' AND table_name like '%0'
					  ORDER BY table_name DESC LIMIT 1) 
					  UNION
        (SELECT table_name FROM information_schema.tables
                      WHERE table_schema='public' AND table_name like '%1'
					  ORDER BY table_name DESC LIMIT 1)
    """
    print("getting 2 most recent captures")
    
    cur.execute(query)
    tableNames = cur.fetchall()

except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        sys.exit()

#Camera 1 - DB table name
tableNames[0][0]

#Camera 2 - DB table name
tableNames[1][0]