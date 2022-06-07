import sqlite as sql
import asyncio
from web3 import Web3

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from dotenv import dotenv_values

config = dotenv_values(".env")
RPC_KEY = config['RPC_API']
BOT_KEY = config['BOT_API']

w3 = Web3(Web3.HTTPProvider(f'https://eth-mainnet.alchemyapi.io/v2/{RPC_KEY}'))
gnosis = Web3(Web3.HTTPProvider('https://rpc.ankr.com/gnosis'))

balance_ABI = [
  {"inputs":[{"type":"uint256","name":"arg0"}],"name":"balances","outputs":[{"type":"uint256","name":""}],"stateMutability":"view","type":"function"},
  {"inputs":[{"type":"uint256","name":"arg0"}],"name":"coins","outputs":[{"type":"address","name":""}],"stateMutability":"view","type":"function"},
  {"inputs":[{"type":"int128","name":"i"},{"type":"int128","name":"j"},{"type":"uint256","name":"dx"}],"name":"get_dy","outputs":[{"type":"uint256","name":""}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"get_virtual_price","outputs":[{"type":"uint256","name":""}],"stateMutability":"view","type":"function"}
]

renBTC_ABI =  [
  {"inputs":[{"type":"int128","name":"arg0"}],"name":"coins","outputs":[{"type":"address","name":""}],"constant":True,"payable":False,"type":"function"},
  {"inputs":[{"type":"int128","name":"arg0"}],"name":"balances","outputs":[{"type":"uint256","name":""}],"constant":True,"payable":False,"type":"function"},
  {"inputs":[{"type":"int128","name":"i"},{"type":"int128","name":"j"},{"type":"uint256","name":"dx"}],"name":"get_dy","outputs":[{"type":"uint256","name":""}],"constant":True,"payable":False,"type":"function"}
]

token_ABI = [
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"stateMutability":"view","name":"decimals","outputs":[{"type":"uint256","name":""}],"type":"function"}
]

class pool:
    def __init__(self, pool_name, contract):
        self.contract_addy = contract
        if (contract == '0x93054188d876f558f4a66B2EF1d97d16eDf0895B'):
            self.contract = w3.eth.contract(address = self.contract_addy, abi = renBTC_ABI)
        else:
            self.contract = w3.eth.contract(address = self.contract_addy, abi = balance_ABI)
        
        self.pool_name = pool_name.lower()
        
        self.token0 = self.contract.caller.coins(0)
        if (self.token0 == '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'):
            self.token0 = 'ETH'
            self.token0_decimal = 18
        else:
            token0_contract = w3.eth.contract(address = self.token0, abi = token_ABI)
            self.token0 = token0_contract.caller.symbol()
            self.token0_decimal = token0_contract.caller.decimals()
        
        self.token1 = self.contract.caller.coins(1)
        if (self.token1 == '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'):
            self.token1 = 'ETH'
            self.token1_decimal = 18
        else:
            token1_contract = w3.eth.contract(address = self.token1, abi = token_ABI)
            self.token1 = token1_contract.caller.symbol()
            self.token1_decimal = token1_contract.caller.decimals()
        
        self.filter = w3.eth.filter({"address": self.contract_addy})
        self.lasttxn = 0

    async def updateBalance(self):
        self.token0_bal = self.contract.caller.balances(0) / 10**self.token0_decimal
        self.token1_bal = self.contract.caller.balances(1) / 10**self.token1_decimal
        total = self.token0_bal + self.token1_bal
        token0_per = round(self.token0_bal / total * 100, 2)
        token1_per = round(self.token1_bal / total * 100, 2)
        self.ratio = [token0_per,token1_per]
        self.swap_price = (self.contract.caller.get_dy(0,1,(10**(self.token0_decimal)))) / 10**(self.token1_decimal)
        print(self.token0_bal)
        print(self.token1_bal)
        print(self.swap_price)

        rows = sql.getAlerts(self.pool_name)
        for row in rows:
            if (row[5] == 0):
                if (token0_per > row[3] and row[3] != 0):
                    #sendmessage above
                    sql.updateAlert(row[0], 1)
                elif (token1_per > row[4] and row[4] != 0):
                    #sendmessage above
                    sql.updateAlert(row[0], 1)
            else:
                if (token0_per < row[3] and row[3] != 0):
                    #sendmessage below
                    sql.updateAlert(row[0], 0)
                elif (token1_per < row[4] and row[4] != 0):
                    #sendmessage below
                    sql.updateAlert(row[0], 0)

    async def listen(self):
        print('listening')
        while True:
            await asyncio.sleep(0)
            for event in self.filter.get_new_entries():
                try:
                    if (event.transactionHash.hex() == self.lasttxn):
                        return
                    self.lasttxn = event.transactionHash.hex()
                    print(event.transactionHash.hex())
                    await self.updateBalance()
                except Exception as e: 
                    print(e)

class threepool:
    def __init__(self, pool_name, contract, chain):
        self.contract_addy = contract
        if (chain == 'gno'): 
            self.contract = gnosis.eth.contract(address = self.contract_addy, abi = balance_ABI)
        else:
            self.contract = w3.eth.contract(address = self.contract_addy, abi = balance_ABI)
        self.pool_name = pool_name.lower()
        
        self.token0 = self.contract.caller.coins(0)
        if (chain == 'gno'):
            token0_contract = gnosis.eth.contract(address = self.token0, abi = token_ABI)
        else:
            token0_contract = w3.eth.contract(address = self.token0, abi = token_ABI)
        self.token0 = token0_contract.caller.symbol()
        self.token0_decimal = token0_contract.caller.decimals()
        
        self.token1 = self.contract.caller.coins(1)
        if (chain == 'gno'):
            token1_contract = gnosis.eth.contract(address = self.token1, abi = token_ABI)
        else:
            token1_contract = w3.eth.contract(address = self.token1, abi = token_ABI)
        self.token1 = token1_contract.caller.symbol()
        self.token1_decimal = token1_contract.caller.decimals()

        self.token2 = self.contract.caller.coins(2)
        if (chain == 'gno'):
            token2_contract = gnosis.eth.contract(address = self.token2, abi = token_ABI)
        else:
            token2_contract = w3.eth.contract(address = self.token2, abi = token_ABI)
        self.token2 = token2_contract.caller.symbol()
        self.token2_decimal = token2_contract.caller.decimals()
        
        self.filter = w3.eth.filter({"address": self.contract_addy})
        self.lasttxn = 0

    async def updateBalance(self):
        self.token0_bal = self.contract.caller.balances(0) / 10**self.token0_decimal
        self.token1_bal = self.contract.caller.balances(1) / 10**self.token1_decimal
        self.token2_bal = self.contract.caller.balances(2) / 10**self.token2_decimal
        total = self.token0_bal + self.token1_bal + self.token2_bal
        token0_per = round(self.token0_bal / total * 100, 2)
        token1_per = round(self.token1_bal / total * 100, 2)
        token2_per = round(self.token2_bal / total * 100, 2)
        self.ratio = [token0_per,token1_per,token2_per]
        print(self.token0_bal)
        print(self.token1_bal)
        print(self.token2_bal)

        rows = sql.get3poolAlerts(self.pool_name)
        for row in rows:
            if (row[6] == 0):
                if (token0_per > row[3] and row[3] != 0):
                    #sendmessage above
                    sql.updateAlert(row[0], 1)
                elif (token1_per > row[4] and row[4] != 0):
                    #sendmessage above
                    sql.updateAlert(row[0], 1)
                elif (token2_per > row[5] and row[5] != 0):
                    #sendmessage above
                    sql.updateAlert(row[0], 1)
            else:
                if (token0_per < row[3] and row[3] != 0):
                    #sendmessage below
                    sql.updateAlert(row[0], 0)
                elif (token1_per < row[4] and row[4] != 0):
                    #sendmessage below
                    sql.updateAlert(row[0], 0)
                elif (token2_per < row[5] and row[5] != 0):
                    #sendmessage above
                    sql.updateAlert(row[0], 0)

    async def listen(self):
        print('listening')
        while True:
            await asyncio.sleep(0)
            for event in self.filter.get_new_entries():
                try:
                    if (event.transactionHash.hex() == self.lasttxn):
                        return
                    self.lasttxn = event.transactionHash.hex()
                    print(event.transactionHash.hex())
                    await self.updateBalance()
                except Exception as e: 
                    print(e)

three_pool = threepool('3pool', '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7', 'eth')
asyncio.run(three_pool.updateBalance())

gno_pool = threepool('gno_pool', '0x7f90122BF0700F9E7e1F688fe926940E8839F353', 'gno')
asyncio.run(gno_pool.updateBalance())

frax_pool = pool('frax','0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B')
asyncio.run(frax_pool.updateBalance())

steth_pool = pool('steth','0xDC24316b9AE028F1497c275EB9192a3Ea0f67022')
asyncio.run(steth_pool.updateBalance())

usdd_pool = pool('usdd','0xe6b5CC1B4b47305c58392CE3D359B10282FC36Ea')
asyncio.run(usdd_pool.updateBalance())

renBTC_pool = pool('renBTC', '0x93054188d876f558f4a66B2EF1d97d16eDf0895B');
asyncio.run(renBTC_pool.updateBalance())

loop = asyncio.get_event_loop()
asyncio.set_event_loop(loop)
asyncio.create_task(three_pool.listen())
asyncio.create_task(gno_pool.listen())
asyncio.create_task(frax_pool.listen())
asyncio.create_task(steth_pool.listen())
asyncio.create_task(usdd_pool.listen())
asyncio.create_task(renBTC_pool.listen())
print(loop.is_running())
print('test')
current_pools = [frax_pool,usdd_pool,steth_pool,renBTC_pool]