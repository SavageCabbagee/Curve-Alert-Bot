const ethers = require("ethers");
const TeleBot = require("telebot");
var sqlite = require("./modules/sqlite");

const RPC = new ethers.providers.JsonRpcProvider("https://mainnet.infura.io/v3/");

const balance_API = [
  {"inputs":[{"type":"uint256","name":"arg0"}],"name":"balances","outputs":[{"type":"uint256","name":""}],"stateMutability":"view","type":"function"}
];

class pool {
    pool_name;
    token0;
    token1;
    token0_bal;
    token1_bal;
    ratio;
    contract;
    filter;
    lasttxn;
    constructor(pool_name, token0, token1, token0_bal, token1_bal, ratio, contract) {
      this.pool_name = pool_name;
      this.token0 = token0;
      this.token1 = token1;
      this.token0_bal = token0_bal;
      this.token1_bal = token1_bal;
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
              if (this.pool_name == 'steth') {
                console.log('whyyy');
                console.log(rows[i]);
                bot.sendMessage(rows[i].chatid, `Alert for stETH triggered! ETH is above ${rows[i].token0}%`)
                sqlite.updateAlert(rows[i].id, 1)
              } else {
                bot.sendMessage(rows[i].chatid, `Alert for ${this.pool_name} triggered! ${this.pool_name} is above ${rows[i].token0}%`)
                sqlite.updateAlert(rows[i].id, 1)
              }
            } else if (token1_per > rows[i].token1 && rows[i].token1 != 0) {
              if (this.pool_name == 'steth') {
                bot.sendMessage(rows[i].chatid, `Alert for stETH triggered! stETH is above ${rows[i].token1}%`)
                sqlite.updateAlert(rows[i].id, 1)
              } else {
                bot.sendMessage(rows[i].chatid, `Alert for  triggered! 3CRV is above ${rows[i].token1}%`)
                sqlite.updateAlert(rows[i].id, 1)
              }
            }
          } else {
            if (token0_per < rows[i].token0 && rows[i].token0 != 0) {
              if (this.pool_name == 'steth') {
                bot.sendMessage(rows[i].chatid, `Alert for stETH triggered! ETH is below ${rows[i].token0}%`)
                sqlite.updateAlert(rows[i].id, 0)
              } else {
                bot.sendMessage(rows[i].chatid, `Alert for ${this.pool_name} triggered! ${this.pool_name} is below ${rows[i].token0}%`)
                sqlite.updateAlert(rows[i].id, 0)
              }
            } else if (token1_per < rows[i].token1 && rows[i].token1 != 0) {
              if (this.pool_name == 'steth') {
                bot.sendMessage(rows[i].chatid, `Alert for stETH triggered! stETH is below ${rows[i].token1}%`)
                sqlite.updateAlert(rows[i].id, 0)
              } else {
                bot.sendMessage(rows[i].chatid, `Alert for ${this.pool_name} triggered! 3CRV is below ${rows[i].token1}%`)
                sqlite.updateAlert(rows[i].id, 0)
              }
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
  filter;
  lasttxn;
  constructor(pool_name, token0_bal, token1_bal, token2_bal, ratio, contract) {
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
three_pool.update_balance()
three_pool.listen();

const frax_pool = new pool('frax','FRAX','3CRV',0,0,[0,0],'0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B');
frax_pool.update_balance()
frax_pool.listen();

const steth_pool = new pool('steth','ETH','stETH',0,0,[0,0],'0xDC24316b9AE028F1497c275EB9192a3Ea0f67022');
steth_pool.update_balance()
steth_pool.listen();

const usdd_pool = new pool('usdd','USDD','3CRV',0,0,[0,0],'0xe6b5cc1b4b47305c58392ce3d359b10282fc36ea');
usdd_pool.update_balance()
usdd_pool.listen();


async function addAlert(poolid, chatid, token0, token1, token2) {
  if (poolid == '3pool') {
    sqlite.add3poolAlert(chatid, token0, token1, token2);
  } else {
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

const bot = new TeleBot('');

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
