import sqlite3

con = sqlite3.connect('test.db')

cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS threepool (id INTEGER NOT NULL PRIMARY KEY, poolid TEXT, chatid varchar(255) NOT NULL, token0 int, token1 int, token2 int, triggered int NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS alerts (id INTEGER NOT NULL PRIMARY KEY, poolid TEXT, chatid varchar(255) NOT NULL, token0 int, token1 int, triggered int NOT NULL)")
con.commit()

cur.execute("INSERT INTO alerts (poolid, chatid, token0, token1, triggered) VALUES ('0',12345,0, 0,0)")
con.commit()
def getAlerts(pool_name):
    rows = cur.execute("SELECT * FROM alerts where poolid = :pool",{"pool": pool_name}).fetchall()
    return rows

def get3poolAlerts(pool_name):
    rows = cur.execute("SELECT * FROM threepool where poolid = :pool",{"pool": pool_name}).fetchall()
    return rows

def updateAlert(id_num, triggered):
    cur.execute("UPDATE alerts SET triggered = :triggered_ WHERE id = :idnum", {
      "idnum": id_num,
      "triggered_": triggered})
    con.commit()

def update3poolAlert(id_num, triggered):
    cur.execute("UPDATE threepool SET triggered = :triggered_ WHERE id = :idnum", {
      "idnum": id_num,
      "triggered_": triggered})
    con.commit()

def addAlert(pool_name, chat_id, token_0, token_1):
    cur.execute("INSERT INTO alerts (poolid, chatid, token0, token1, triggered) VALUES (:pool, :chatid, :token0, :token1, 0)", {
      "pool": pool_name,
      "chatid": chat_id,
      "token0": token_0,
      "token1": token_1
    })
    con.commit()

def add3poolAlert(pool_name, chat_id, token_0, token_1, token_2):
    cur.execute("INSERT INTO threepool (chatid, token0, token1, token2, triggered) VALUES (:chatid, :token0, :token1, :token2, 0)", {
      "pool": pool_name,
      "chatid": chat_id,
      "token0": token_0,
      "token1": token_1,
      "token2": token_2
    })
    con.commit()

def removeAlert(pool_name, chat_id):
    cur.execute("DELETE FROM alerts WHERE chatid = :chatid AND poolid = :pool", {
      "pool": pool_name,
      "chatid": chat_id
    })
    con.commit()

def remove3poolAlert(pool_name, chat_id):
    cur.execute("DELETE FROM threepool WHERE chatid = :chatid AND poolid = :pool", {
      "pool": pool_name,
      "chatid": chat_id
    })
    con.commit()