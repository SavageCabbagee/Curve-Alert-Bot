var sqlite3 = require("sqlite3").verbose();
var db = new sqlite3.Database("database.db");

db.run("CREATE TABLE IF NOT EXISTS threepool (id INTEGER NOT NULL PRIMARY KEY, chatid varchar(255) NOT NULL, token0 int NOT NULL, token1 int NOT NULL, token2 int NOT NULL, triggered int NOT NULL)");
db.run("CREATE TABLE IF NOT EXISTS alerts (id INTEGER NOT NULL PRIMARY KEY, poolid TEXT, chatid varchar(255) NOT NULL, token0 int NOT NULL, token1 int NOT NULL, triggered int NOT NULL)");
/*
const yes = db.all("SELECT * FROM alerts where poolid = $pool", {
  $pool: 'usdd'
},function(err, rows) {
  console.log(rows);
  console.log(typeof rows);
  console.log(rows.length);
  return rows;
});
*/

module.exports = {
  getAlerts: async function(pool_name:string, fn){
    await db.all("SELECT * FROM alerts where poolid = $pool", {
      $pool: pool_name
    },function(err, rows) {
      fn(rows);
    });
  },

  get3poolAlerts: async function(fn){
    await db.all("SELECT * FROM threepool",function(err, rows) {
      fn(rows);
    });
  },

  updateAlert: async function(id_num:any, triggered:any) {
    await db.all("UPDATE alerts SET triggered = $triggered WHERE id = $idnum", {
      $idnum: id_num,
      $triggered: triggered
    });
  },

  update3poolAlert: async function(id_num:any, triggered:any) {
    await db.all("UPDATE threepool SET triggered = $triggered WHERE id = $idnum", {
      $idnum: id_num,
      $triggered: triggered
    });
  },

  addAlert: function(pool_name:string, chat_id:any, token_0:any, token_1:any){
    db.run("INSERT INTO alerts (poolid, chatid, token0, token1, triggered) VALUES ($pool, $chatid, $token0, $token1, 0)", {
      $pool: pool_name,
      $chatid: chat_id,
      $token0: token_0,
      $token1: token_1
    });
  },

  add3poolAlert: function(chat_id:any, token_0:any, token_1:any, token_2:any){
    db.run("INSERT INTO threepool (chatid, token0, token1, token2, triggered) VALUES ($chatid, $token0, $token1, $token2, 0)", {
      $chatid: chat_id,
      $token0: token_0,
      $token1: token_1,
      $token2: token_2
    });
  },

  removeAlert: function(pool_name:string, chat_id:any){
    db.run("DELETE FROM alerts WHERE chatid = $chatid AND poolid = $pool", {
      $pool: pool_name,
      $chatid: chat_id
    })
  },

  remove3poolAlert: function(chat_id:any){
    db.run("DELETE FROM threepool WHERE chatid = $chatid", {
      $chatid: chat_id
    })
  }
}