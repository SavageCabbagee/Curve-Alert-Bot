const ethers = require("ethers");
const TeleBot = require("telebot");
var sqlite = require("./modules/sqlite");

const RPC = new ethers.providers.JsonRpcProvider("https://eth-mainnet.alchemyapi.io/v2/FL1ROrwlt725zM099BqijvuuP8W63FYE");

const balance_API = [
  {"inputs":[{"type":"uint256","name":"arg0"}],"name":"balances","outputs":[{"type":"uint256","name":""}],"stateMutability":"view","type":"function"},
  {"inputs":[{"type":"uint256","name":"arg0"}],"name":"coins","outputs":[{"type":"address","name":""}],"stateMutability":"view","type":"function"}
];

const token_API = [
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}
]

class pool {
    pool_name;
    token0;
    token1;
    token0_bal;
    token1_bal;
    ratio;
    contract;
    contract_addy;
    filter;
    lasttxn;
    constructor(pool_name, contract) {
      this.contract_addy = contract;
      this.contract = new ethers.Contract(
        contract,
        balance_API,
        RPC
      );
      this.pool_name = pool_name.toLowerCase();

      this.token0 = (this.contract.coins(0)).then(
        value => {
          if (value == '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE') {
            this.token0 = 'ETH';
            return;
          };
          console.log(value)
          let token_contract = new ethers.Contract(
            String(value),
            token_API,
            RPC
          );
          this.token0 = (token_contract.symbol()).then(
            value => {
              this.token0 = value;
              console.log(this.token0);
            }
          );
        });

      this.token1 = (this.contract.coins(1)).then(
        value => {
          if (value == '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE') {
            this.token0 = 'ETH';
            return;
          };
          let token_contract = new ethers.Contract(
            String(value),
            token_API,
            RPC
          );
          this.token1 = (token_contract.symbol()).then(
            value => {
              this.token1 = value;
              console.log(this.token1);
            }
          );
        });

      
      this.filter = {address: contract};
      this.lasttxn = 0
    }

    async update_balance() {
      this.token0_bal = Number(await this.contract.balances(0)) / 10**18;
      this.token1_bal = Number(await this.contract.balances(1)) / 10**18;
      var total = this.token0_bal + this.token1_bal;
      var token0_per = (this.token0_bal / total * 100).toFixed(2);
      var token1_per = (this.token1_bal / total * 100).toFixed(2);
      this.ratio = [token0_per, token1_per];
      console.log(this.token0_bal);
      console.log(this.token1_bal);
      console.log(this.ratio);

      sqlite.getAlerts(this.pool_name, (rows) => {
        for (let i =0; i<rows.length; i++) {
          if (rows[i].triggered == 0) {
            if (token0_per > rows[i].token0 && rows[i].token0 != 0) {
              bot.sendMessage(rows[i].chatid, `Alert for ${this.pool_name} triggered! ${this.token0} is above ${rows[i].token0}%`)
              sqlite.updateAlert(rows[i].id, 1)
            } else if (token1_per > rows[i].token1 && rows[i].token1 != 0) {
              bot.sendMessage(rows[i].chatid, `Alert for ${this.pool_name} triggered! ${this.token1} is above ${rows[i].token1}%`)
              sqlite.updateAlert(rows[i].id, 1)
            }
          } else {
            if (token0_per < rows[i].token0 && rows[i].token0 != 0) {
              bot.sendMessage(rows[i].chatid, `Alert for ${this.pool_name} triggered! ${this.token0} is below ${rows[i].token0}%`)
              sqlite.updateAlert(rows[i].id, 0)
            } else if (token1_per < rows[i].token1 && rows[i].token1 != 0) {
              bot.sendMessage(rows[i].chatid, `Alert for ${this.pool_name} triggered! ${this.token1} is below ${rows[i].token1}%`)
              sqlite.updateAlert(rows[i].id, 0) 
            }
          }
        }
      })
    }

    async listen() {
      RPC.on(this.filter, async (event: any) => {
        try {
          if (this.lasttxn == event.transactionHash) {
            return;
          }
          this.lasttxn = event.transactionHash;
          console.log(this.lasttxn);
          console.log('txn')
          await this.update_balance();
        } catch(err) {
          return;
        }
      })
    }
};

class threepool {
  pool_name;
  token0_bal;
  token1_bal;
  token2_bal;
  ratio;
  contract;
  contract_addy;
  filter;
  lasttxn;
  constructor(pool_name, token0_bal, token1_bal, token2_bal, ratio, contract) {
    this.contract_addy = contract;
    this.pool_name = pool_name;
    this.token0_bal = token0_bal;
    this.token1_bal = token1_bal;
    this.token2_bal = token2_bal;
    this.ratio = ratio;
    this.contract = new ethers.Contract(
      contract,
      balance_API,
      RPC
    );
    this.filter = {address: contract};
    this.lasttxn = 0
  }

  async update_balance() {
    this.token0_bal = Number(await this.contract.balances(0)) / 10**18;
    this.token1_bal = Number(await this.contract.balances(1)) / 10**6;
    this.token2_bal = Number(await this.contract.balances(2)) / 10**6;
    var total = this.token0_bal + this.token1_bal + this.token2_bal;
    var token0_per = (this.token0_bal / total * 100).toFixed(2);
    var token1_per = (this.token1_bal / total * 100).toFixed(2);
    var token2_per = (this.token2_bal / total * 100).toFixed(2);
    this.ratio = [token0_per, token1_per, token2_per];
    console.log(this.token0_bal);
    console.log(this.token1_bal);
    console.log(this.token2_bal);
    console.log(this.ratio);
    sqlite.get3poolAlerts((rows) => {
      for (let i =0; i<rows.length; i++) {
        if (rows[i].triggered == 0) {
          console.log(token1_per);
          if (token0_per > rows[i].token0 && rows[i].token0 != 0) {
            bot.sendMessage(rows[i].chatid, `Alert for 3pool triggered! DAI is above ${rows[i].token0}%`)
            sqlite.update3poolAlert(rows[i].id, 1)
          } else if (token1_per > rows[i].token1 && rows[i].token1 != 0) {
            bot.sendMessage(rows[i].chatid, `Alert for 3pool triggered! USDC is above ${rows[i].token1}%`)
            sqlite.update3poolAlert(rows[i].id, 1)
          } else if (token2_per > rows[i].token2 && rows[i].token2 != 0) {
            bot.sendMessage(rows[i].chatid, `Alert for 3pool triggered! USDT is above ${rows[i].token2}%`)
            sqlite.update3poolAlert(rows[i].id, 1)
          }
        } else {
          if (token0_per < rows[i].token0 && rows[i].token0 != 0) {
            bot.sendMessage(rows[i].chatid, `Alert for 3pool triggered! DAI is below ${rows[i].token0}%`)
            sqlite.update3poolAlert(rows[i].id, 0)
          } else if (token1_per < rows[i].token1 && rows[i].token1 != 0) {
            bot.sendMessage(rows[i].chatid, `Alert for 3pool triggered! USDC is below ${rows[i].token1}%`)
            sqlite.update3poolAlert(rows[i].id, 0)
          } else if (token2_per < rows[i].token2 && rows[i].token2 != 0) {
            bot.sendMessage(rows[i].chatid, `Alert for 3pool triggered! USDT is below ${rows[i].token2}%`)
            sqlite.update3poolAlert(rows[i].id, 0)
          }
        }
      }
    })
  }

  async listen() {
    RPC.on(this.filter, async (event: any) => {
      try {
        if (this.lasttxn == event.transactionHash) {
          return;
        }
        this.lasttxn = event.transactionHash;
        console.log(this.lasttxn);
        console.log('txn')
        await this.update_balance();
      } catch(err) {
        return;
      }
    })
  }
};

const three_pool = new threepool('3pool',0,0,0,[0,0,0],'0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7');
//three_pool.update_balance()
//three_pool.listen();

const frax_pool = new pool('frax','0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B');
//frax_pool.update_balance()
//frax_pool.listen();

const steth_pool = new pool('steth','0xDC24316b9AE028F1497c275EB9192a3Ea0f67022');
//steth_pool.update_balance()
//steth_pool.listen();

const usdd_pool = new pool('usdd','0xe6b5cc1b4b47305c58392ce3d359b10282fc36ea');
//usdd_pool.update_balance()
//usdd_pool.listen();

var current_pools = [three_pool,frax_pool,steth_pool,usdd_pool];

async function addAlert(poolid, chatid, token0, token1, token2) {
  if (poolid == '3pool') {
    sqlite.add3poolAlert(chatid, token0, token1, token2);
  } else {
    poolid = poolid.toLowerCase()
    sqlite.addAlert(poolid, chatid, token0, token1);
  }
};

async function removeAlert(poolid, chatid) {
  if (poolid == '3pool') {
    sqlite.remove3poolAlert(chatid);
  } else {
    sqlite.removeAlert(poolid, chatid);
  }
};

function addPool(poolname, contract){
  for (let i =0; i<current_pools.length; i++) {
    var a_pool = current_pools[i]
    if (a_pool.contract_addy == contract) {
      console.log(`Pool already added, pool name is ${a_pool.pool_name}`);
      return;
    }
  }
  sqlite.addPool(poolname.toLowerCase(),contract);
  let new_pool = new pool(poolname, contract);
    
}

addPool('renBTC','0x93054188d876f558f4a66B2EF1d97d16eDf0895B');
addPool('renBTC','0x93054188d876f558f4a66B2EF1d97d16eDf0895B');
addPool('renBTC','0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B');

const bot = new TeleBot('5392288525:AAH8YCZ0dwWzaaFkwlfy8AUOAsb96QF8CQE');
/*
bot.on('/reserves', msg => {
  let id = msg.chat.id;
  let text = msg.text.slice(10).toLowerCase();
  if (text == 'usdd') {
    return bot.sendMessage(id, 
      `USDD: ${usdd_pool.token0_bal.toLocaleString()} (${usdd_pool.ratio[0]}%)\n3CRV: ${usdd_pool.token1_bal.toLocaleString()} (${usdd_pool.ratio[1]}%)`);
  } else if (text == 'frax') {
    return bot.sendMessage(id, 
      `FRAX: ${frax_pool.token0_bal.toLocaleString()} (${frax_pool.ratio[0]}%)\n3CRV: ${frax_pool.token1_bal.toLocaleString()} (${frax_pool.ratio[1]}%)`);
  } else if (text == 'steth') {
    return bot.sendMessage(id, 
      `ETH: ${steth_pool.token0_bal.toLocaleString()} (${steth_pool.ratio[0]}%)\nstETH: ${steth_pool.token1_bal.toLocaleString()} (${steth_pool.ratio[1]}%)`);
  } else if (text == '3pool') {
    return bot.sendMessage(id, 
      `DAI: ${three_pool.token0_bal.toLocaleString()} (${three_pool.ratio[0]}%)\nUSDC: ${three_pool.token1_bal.toLocaleString()} (${three_pool.ratio[1]}%)\nUSDT: ${three_pool.token2_bal.toLocaleString()} (${three_pool.ratio[2]}%)`);
  } else if (text == '') {
    return bot.sendMessage(id, 
      `DAI: ${three_pool.token0_bal.toLocaleString()} (${three_pool.ratio[0]}%)\nUSDC: ${three_pool.token1_bal.toLocaleString()} (${three_pool.ratio[1]}%)\nUSDT: ${three_pool.token2_bal.toLocaleString()} (${three_pool.ratio[2]}%)\n\nUSDD: ${usdd_pool.token0_bal.toLocaleString()} (${usdd_pool.ratio[0]}%)\n3CRV: ${usdd_pool.token1_bal.toLocaleString()} (${usdd_pool.ratio[1]}%)\n\nFRAX: ${frax_pool.token0_bal.toLocaleString()} (${frax_pool.ratio[0]}%)\n3CRV: ${frax_pool.token1_bal.toLocaleString()} (${frax_pool.ratio[1]}%)\n\nETH: ${steth_pool.token0_bal.toLocaleString()} (${steth_pool.ratio[0]}%)\nstETH: ${steth_pool.token1_bal.toLocaleString()} (${steth_pool.ratio[1]}%)`);
  } else {
    return bot.sendMessage(id, 
      `Sorry, not recognized\nCurrent recognized pools are:\n3pool\nFRAX\nUSDD\nstETH`);
  }
});

bot.on('/addalert',msg => {
  //id is a int/number
  let id = msg.chat.id;
  let text = msg.text.slice(10).toLowerCase().split(',');
  if (text.length > 4) {
    console.log('Error1');
    return bot.sendMessage(id, `Error, too many variables`);
  };
  try {
    if (text[0] == '3pool') {
      if (!((text[1] == 0 && text[2] == 0) || (text[1] == 0 && text[3] == 0) || (text[2] == 0 && text[3] == 0))) {
        return bot.sendMessage(id, `Error, 2 of the token balance must be 0!`);
      }
      addAlert('3pool', id, text[1], text[2], text[3]);
      return bot.sendMessage(id, `3pool alert added!`);
    } else {
      if (!((text[1] == 0 || (text[2] == 0)))) {
        return bot.sendMessage(id, `Error, 1 of the token balance must be 0!`);
      }
      addAlert(text[0], id, text[1], text[2], 0);
      return bot.sendMessage(id, `${text[0]} alert added!`);
    };
  } catch {
    console.log('Error2');
    return bot.sendMessage(id, `Error2`);
  }
});

bot.on('/removealert',msg => {
  //id is a int/number
  let id = msg.chat.id;
  let text = msg.text.slice(13);
  console.log(text);
  try {
    if (text == '3pool') {
      removeAlert('3pool', id);
      return bot.sendMessage(id, `All 3pool alerts removed!`);
    } else {
      removeAlert(text, id);
      return bot.sendMessage(id, `All ${text} alerts removed!`);
    };
  } catch {
    console.log('Error3');
    return bot.sendMessage(id, `Error3`);
  }
});

bot.on('/getalert',msg => {
  //id is a int/number
  let id = msg.chat.id;
  let text = msg.text.slice(10);
  let message = [`Your ${text} alerts are:`];
  try {
    if (text == '3pool'){
      sqlite.get3poolAlerts(function(rows) {
        for (let i =0; i<rows.length; i++) {
          if (rows[i].chatid == id) {
            message.push(`DAI:${rows[i].token0}% USDC:${rows[i].token1}% USDT:${rows[i].token2}%`)
          }
        }
        var message_sent = message.join('\n');
        return bot.sendMessage(id, message_sent);  
      });
    } else {
      sqlite.getAlerts(text, function(rows) {
        for (let i =0; i<rows.length; i++) {
          if (rows[i].chatid == id) {
            if (text == 'steth') {
              message.push(`ETH:${rows[i].token0}% stETH:${rows[i].token1}%`);
            } else {
              message.push(`${text}:${rows[i].token0}% 3CRV:${rows[i].token1}%`);
              console.log(message);
            }
          }
        }
        var message_sent = message.join('\n');
        return bot.sendMessage(id, message_sent);      
      });
    }
  } catch {
    console.log('Error4');
    return bot.sendMessage(id, `Error4`);
  }
});

bot.start();






/*
const frax_pool = new ethers.Contract(
    '0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B',
    balance_API,
    RPC
  );

const lusd_pool = new ethers.Contract(
  '0xEd279fDD11cA84bEef15AF5D39BB4d4bEE23F0cA',
  balance_API,
  RPC
);

async function frax_balance() {
    var frax = await frax_pool.balances(0);
    var three_pool = await frax_pool.balances(1);
    frax = Number(frax) / 10**18;
    three_pool = Number(three_pool) / 10**18;
    var total = frax + three_pool;
    var frax_per = (frax / total * 100).toFixed(2);
    var three_per = (three_pool / total * 100).toFixed(2);
    var ratio = [frax_per, three_per];
    console.log( 
      'Frax: ' + frax.toLocaleString() + '(' + frax_per + '%)' +
      '\n3CRV: ' + three_pool.toLocaleString() + '(' + three_per + '%)' +
      '\nratio: ' + ratio[0] + ',' + ratio[1]
    )      
};

async function lusd_balance() {
  var lusd = await lusd_pool.balances(0);
  var three_pool = await lusd_pool.balances(1);
  lusd = Number(lusd) / 10**18;
  three_pool = Number(three_pool) / 10**18;
  var total = lusd + three_pool;
  var lusd_per = (lusd / total * 100).toFixed(2);
  var three_per = (three_pool / total * 100).toFixed(2);
  var ratio = [lusd_per, three_per];
  console.log( 
    'LUSD: ' + lusd.toLocaleString() + '(' + lusd_per + '%)' +
    '\n3CRV: ' + three_pool.toLocaleString() + '(' + three_per + '%)' +
    '\nratio: ' + ratio[0] + ',' + ratio[1]
  )      
};

//frax_balance();
//lusd_balance();
*/

/*
const res = sqlite.getAlerts('frax', function(rows) {
  for (let i =0; i<rows.length; i++) {
    console.log(rows[i].chatid)
  }
});
const res = sqlite.addAlert('frax', '23',60,40);
const res = sqlite.removeAlert('frax', '4444');
const res = sqlite.add3poolAlert('23',60,20,20);
const res = sqlite.get3poolAlerts(function(rows) {
  for (let i =0; i<rows.length; i++) {
    console.log(rows[i].chatid)
  }
});
const res = sqlite.remove3poolAlert('23');
const res = sqlite.updateAlert('usdd','2',0);
const res1 = sqlite.update3poolAlert('23',1);
*/