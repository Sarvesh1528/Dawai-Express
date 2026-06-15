import datetime, sqlite3

def create_table():
    conn = sqlite3.connect('Laptop\\Databases\\patData.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS patient(
        patName text,
        patEmail text,        
        bedNum int,
        patDisease text,
        dos1 int,
        dos2 int,
        dos3 int,
        dos4 int,
        date_created timestamp  
    )
    """)
    conn.commit()
    conn.close()

def sort():
    conn = sqlite3.connect('Prioritize.db')
    c = conn.cursor()
    c.execute("SELECT pending FROM customers ORDER BY last_name DESC")
    conn.commit()
    # Query the database order by
    # c.execute("SELECT rowid,* FROM customers")# Typesof datatypes in sqlite3: null, int, real, text, blob
    items = c.fetchall()
    for item in items:
        print(item)
    # Commit our commands
    conn.commit()
    conn.close()

def delete_table(name):
    conn = sqlite3.connect('Laptop\\Databases\\patData.db')
    c = conn.cursor()
    c.execute("DROP TABLE " + name)
    conn.commit()
    conn.close()

def add_data(name, email, bed, disease, dos1, dos2, dos3, dos4):
    conn = sqlite3.connect('Laptop\\Databases\\patData.db')
    c = conn.cursor()
    c.execute("INSERT INTO patient (patName, patEmail, bedNum, patDisease, dos1, dos2, dos3, dos4, date_created) VALUES (?,?,?,?,?,?,?,?,?)", (name, email, bed, disease, dos1, dos2, dos3, dos4, datetime.datetime.now()))
    print("Command executed sucessfully...")
    conn.commit()
    conn.close()

def delete(name,email):
    conn = sqlite3.connect('Laptop\\Databases\\patData.db')
    c = conn.cursor()
    c.execute("DELETE from " + name + " WHERE patEmail = ?", (email,))
    conn.commit()

def update():
    conn = sqlite3.connect('Prioritize.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET due_y = 2021 WHERE rowid = 1")
    conn.commit()
    conn.close()

def fetch_data(dataType):
    conn = sqlite3.connect('Laptop\\Databases\\patData.db')
    c = conn.cursor()
    pats = c.execute("SELECT " + dataType + " FROM patient ORDER BY bedNum").fetchall()
    print("Command executed sucessfully...")
    conn.commit()
    conn.close()
    return(pats)

def get_pats():
    conn = sqlite3.connect('Laptop\\Databases\\patData.db')
    c = conn.cursor()
    pats = c.execute("SELECT * FROM patient ORDER BY bedNum").fetchall()
    print(pats)
    print()
    payload = []
    for i in pats:
        # print("Name: ", i[0], "Bed Num:", i[2], "Dosage", i[4], i[5], i[6], i[7])
        payload.append([i[0], i[2], i[4], i[5], i[6], i[7]])
    conn.commit()
    conn.close()
    return(payload)

if __name__ == '__main__':
    # print(fetch_data("bedNum"))
    # print([x[0] for x in fetch_data("patName")])
    # delete("patient", 5)
    # delete_table("patient")
    patList = get_pats()
    patDict = {}
    for i,j in enumerate(patList):
        print(i, j)
        patDict[i] = j
    print(patDict)

        