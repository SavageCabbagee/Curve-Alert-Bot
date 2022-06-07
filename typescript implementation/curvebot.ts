const ethers = require("ethers");
const TeleBot = require("telebot");
var sqlite = require("./modules/sqlite");

const RPC = new ethers.providers.JsonRpcProvider("");

const balance_ABI = [
  {"inputs":[{"type":"uint256","name":"arg0"}],"name":"balances","outputs":[{"type":"uint256","name":""}],"stateMutability":"view","type":"function"},
  {"inputs":[{"type":"uint256","name":"arg0"}],"name":"coins","outputs":[{"type":"address","name":""}],"stateMutability":"view","type":"function"},
  {"inputs":[{"type":"int128","name":"i"},{"type":"int128","name":"j"},{"type":"uint256","name":"dx"}],"name":"get_dy","outputs":[{"type":"uint256","name":""}],"stateMutability":"view","type":"function"}
];

const renBTC_ABI =  [
  {"inputs":[{"type":"int128","name":"arg0"}],"name":"coins","outputs":[{"type":"address","name":""}],"constant":true,"payable":false,"type":"function"},
  {"inputs":[{"type":"int128","name":"arg0"}],"name":"balances","outputs":[{"type":"uint256","name":""}],"constant":true,"payable":false,"type":"function"},
  {"inputs":[{"type":"int128","name":"i"},{"type":"int128","name":"j"},{"type":"uint256","name":"dx"}],"name":"get_dy","outputs":[{"type":"uint256","name":""}],"constant":true,"payable":false,"type":"function"}
];

const token_ABI = [
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"stateMutability":"view","name":"decimals","outputs":[{"type":"uint256","name":""}],"type":"function"}
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
    token0_decimal;
    token1_decimal;
    swap_price;
    constructor(pool_name, contract) {
      this.contract_addy = contract;
      if (contract == '0x93054188d876f558f4a66B2EF1d97d16eDf0895B') {
        this.contract = new ethers.Contract(
          contract,
          renBTC_ABI,
          RPC
        );
      } else {
        this.contract = new ethers.Contract(
          contract,
          balance_ABI,
          RPC
        );
      }
      
      this.pool_name = pool_name.toLowerCase();

      this.token0 = (this.contract.coins(0)).then(
        value => {
          if (value == '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE') {
            this.token0 = 'ETH';
            this.token0_decimal = 18;
            return;
          };
          console.log(value)
          let token0_contract = new ethers.Contract(
            String(value),
            token_ABI,
            RPC
          );
          this.token0 = (token0_contract.symbol()).then(
            value => {
              this.token0 = value;
              console.log(this.token0);
            }
          );
          this.token0_decimal = (token0_contract.decimals()).then(
            value => {
              this.token0_decimal = Number(value);
            }
          )
        });

      this.token1 = (this.contract.coins(1)).then(
        value => {
          if (value == '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE') {
            this.token1 = 'ETH';
            this.token1_decimal = 18;
            return;
          };
          let token1_contract = new ethers.Contract(
            String(value),
            token_ABI,
            RPC
          );
          this.token1 = (token1_contract.symbol()).then(
            value => {
              this.token1 = value;
              console.log(this.token1);
            }
          );
          this.token1_decimal = (token1_contract.decimals()).then(
            value => {
              this.token1_decimal = Number(value);
              console.log(this.token1_decimal)
            }
          )
        });

      
      this.filter = {address: contract};
      this.lasttxn = 0
    }

    async update_balance() {
      this.token0_bal = Number(await this.contract.balances(0)) / 10**(await this.token0_decimal);
      this.token1_bal = Number(await this.contract.balances(1)) / 10**(await this.token1_decimal);
      var total = this.token0_bal + this.token1_bal;
      var token0_per = (this.token0_bal / total * 100).toFixed(2);
      var token1_per = (this.token1_bal / total * 100).toFixed(2);
      this.ratio = [token0_per, token1_per];
      console.log(this.token0_bal);
      console.log(this.token1_bal);
      console.log(this.ratio);
      this.swap_price = Number(await this.contract.get_dy(0,1,String(10**(this.token0_decimal)))) / 10**(await this.token1_decimal);

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
  token0;
  token1;
  token0_decimal;
  token1_decimal;
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
      balance_ABI,
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
var wait_for_update = setTimeout(() => {
  three_pool.update_balance();;
}, 5000);
three_pool.listen();

const frax_pool = new pool('frax','0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B');
var wait_for_update = setTimeout(() => {
  frax_pool.update_balance();;
}, 5000);
frax_pool.listen();

const steth_pool = new pool('steth','0xDC24316b9AE028F1497c275EB9192a3Ea0f67022');
var wait_for_update = setTimeout(() => {
  steth_pool.update_balance();;
}, 5000);
steth_pool.listen();

const usdd_pool = new pool('usdd','0xe6b5cc1b4b47305c58392ce3d359b10282fc36ea');
var wait_for_update = setTimeout(() => {
  usdd_pool.update_balance();;
}, 5000);
usdd_pool.listen();

const renBTC_pool = new pool('renBTC', '0x93054188d876f558f4a66B2EF1d97d16eDf0895B');
var wait_for_update = setTimeout(() => {
  renBTC_pool.update_balance();;
}, 5000);
renBTC_pool.listen();

let current_pools = [frax_pool,usdd_pool,steth_pool,renBTC_pool];

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

const bot = new TeleBot('');

bot.on('/reserves', msg => {
  let id = msg.chat.id;
  let text = msg.text.slice(10).toLowerCase();
  if (text == '3pool') {
    return bot.sendMessage(id, 
      `DAI: ${three_pool.token0_bal.toLocaleString()} (${three_pool.ratio[0]}%)\nUSDC: ${three_pool.token1_bal.toLocaleString()} (${three_pool.ratio[1]}%)\nUSDT: ${three_pool.token2_bal.toLocaleString()} (${three_pool.ratio[2]}%)`);
  }
  for (let i =0; i<current_pools.length; i++) {
    var a_pool = current_pools[i]
    if (a_pool.pool_name == text) {
      return bot.sendMessage(id,
        `${a_pool.token0}: ${a_pool.token0_bal.toLocaleString()} (${a_pool.ratio[0]}%)\n${a_pool.token1}: ${a_pool.token1_bal.toLocaleString()} (${a_pool.ratio[1]}%)\n1 ${a_pool.token0} -> ${a_pool.swap_price} ${a_pool.token1}`)
      }
    }
  if (text == '') {
    let message = [`DAI: ${three_pool.token0_bal.toLocaleString()} (${three_pool.ratio[0]}%)\nUSDC: ${three_pool.token1_bal.toLocaleString()} (${three_pool.ratio[1]}%)\nUSDT: ${three_pool.token2_bal.toLocaleString()} (${three_pool.ratio[2]}%)`];
    for (let i =0; i<current_pools.length; i++) {
      message.push(`${current_pools[i].token0}: ${current_pools[i].token0_bal.toLocaleString()} (${current_pools[i].ratio[0]}%)\n${current_pools[i].token1}: ${current_pools[i].token1_bal.toLocaleString()} (${current_pools[i].ratio[1]}%)\n1 ${current_pools[i].token0} -> ${current_pools[i].swap_price} ${current_pools[i].token1}`)
    }
    var message_sent = message.join('\n\n');
    return bot.sendMessage(id, message_sent);
  } else {
    return bot.sendMessage(id, 
      `Sorry, not recognized\nCurrent recognized pools are:\n3pool\nFRAX\nUSDD\nstETH\nrenBTC`);
  }
  /*
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
  */
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
      text = text.toLowerCase();
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
