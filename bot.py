
import sqlite as sql
import asyncio
from web3 import Web3

import logging
from threading import Thread
from multicall import Call, Multicall
import time 

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext

from dotenv import dotenv_values

config = dotenv_values(".env")
RPC_KEY = config['RPC_API']
BOT_KEY = config['BOT_API']
logging.basicConfig(filename='logs.log', level = logging.ERROR, format = '%(asctime)s.%(msecs)03d %(funcName)s: %(message)s', datefmt = '%Y-%m-%d %H:%M:%S', )

w3 = Web3(Web3.HTTPProvider(f'https://eth-mainnet.alchemyapi.io/v2/{RPC_KEY}'))
gnosis = Web3(Web3.HTTPProvider('https://rpc.ankr.com/gnosis'))

balance_ABI = [
  {"inputs":[{"type":"uint256","name":"arg0"}],"name":"balances","outputs":[{"type":"uint256","name":""}],"stateMutability":"view","type":"function"},
  {"inputs":[{"type":"uint256","name":"arg0"}],"name":"coins","outputs":[{"type":"address","name":""}],"stateMutability":"view","type":"function"},
  {"inputs":[{"type":"int128","name":"i"},{"type":"int128","name":"j"},{"type":"uint256","name":"dx"}],"name":"get_dy","outputs":[{"type":"uint256","name":""}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"get_virtual_price","outputs":[{"type":"uint256","name":""}],"stateMutability":"view","type":"function"}
]

fraxbp_ABI = [
  {"inputs":[{"type":"uint256","name":"arg0"}],"name":"balances","outputs":[{"type":"uint256","name":""}],"stateMutability":"view","type":"function"},
  {"inputs":[{"type":"uint256","name":"arg0"}],"name":"coins","outputs":[{"type":"address","name":""}],"stateMutability":"view","type":"function"},
  {"inputs":[{"type":"int128","name":"i"},{"type":"int128","name":"j"},{"type":"uint256","name":"_dx"}],"name":"get_dy","outputs":[{"type":"uint256","name":""}],"stateMutability":"view","type":"function"},
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
        elif (contract == '0xDcEF968d416a41Cdac0ED8702fAC8128A64241A2'):
            self.contract = w3.eth.contract(address = self.contract_addy, abi = fraxbp_ABI)
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
        print(f'{self.pool_name} started' )

    async def updateBalance(self):
        rows = sql.getAlerts(self.pool_name)
        for row in rows:
            chat_id = row[2]
            if (row[5] == 0):
                if (self.token0_per > row[3] and row[3] != 0):
                    await bot.send_message(chat_id = chat_id, text = f'Alert for {self.pool_name} triggered! {self.token0} is above {row[3]}%')
                    sql.updateAlert(row[0], 1)
                elif (self.token1_per > row[4] and row[4] != 0):
                    await bot.send_message(chat_id = chat_id, text = f'Alert for {self.pool_name} triggered! {self.token1} is above {row[4]}%')
                    sql.updateAlert(row[0], 1)
            else:
                if (self.token0_per < row[3] and row[3] != 0):
                    await bot.send_message(chat_id = chat_id, text = f'Alert for {self.pool_name} triggered! {self.token0} is below {row[3]}%')
                    sql.updateAlert(row[0], 0)
                elif (self.token1_per < row[4] and row[4] != 0):
                    await bot.send_message(chat_id = chat_id, text = f'Alert for {self.pool_name} triggered! {self.token1} is below {row[3]}%')
                    sql.updateAlert(row[0], 0)

    async def listen(self):
        print('listening')
        while True:
            for event in self.filter.get_new_entries():
                try:
                    if (event.transactionHash.hex() == self.lasttxn):
                        return
                    self.lasttxn = event.transactionHash.hex()
                    print(event.transactionHash.hex())
                    await self.updateBalance()
                except Exception as e: 
                    print(e)
            await asyncio.sleep(10)

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
        print(f'{self.pool_name} started' )

    async def updateBalance(self):
        rows = sql.get3poolAlerts(self.pool_name)
        for row in rows:
            chat_id = row[2]
            if (row[6] == 0):
                if (self.token0_per > row[3] and row[3] != 0):
                    await bot.send_message(chat_id = chat_id, text = f'Alert for {self.pool_name} triggered! {self.token0} is above {row[3]}%')
                    sql.update3poolAlert(row[0], 1)
                elif (self.token1_per > row[4] and row[4] != 0):
                    await bot.send_message(chat_id = chat_id, text = f'Alert for {self.pool_name} triggered! {self.token1} is above {row[4]}%')
                    sql.update3poolAlert(row[0], 1)
                elif (self.token2_per > row[5] and row[5] != 0):
                    await bot.send_message(chat_id = chat_id, text = f'Alert for {self.pool_name} triggered! {self.token2} is above {row[5]}%')
                    sql.update3poolAlert(row[0], 1)
            else:
                if (self.token0_per < row[3] and row[3] != 0):
                    await bot.send_message(chat_id = chat_id, text = f'Alert for {self.pool_name} triggered! {self.token0} is below {row[3]}%')
                    sql.update3poolAlert(row[0], 0)
                elif (self.token1_per < row[4] and row[4] != 0):
                    await bot.send_message(chat_id = chat_id, text = f'Alert for {self.pool_name} triggered! {self.token1} is below {row[4]}%')
                    sql.update3poolAlert(row[0], 0)
                elif (self.token2_per < row[5] and row[5] != 0):
                    await bot.send_message(chat_id = chat_id, text = f'Alert for {self.pool_name} triggered! {self.token2} is below {row[5]}%')
                    sql.update3poolAlert(row[0], 0)

    async def listen(self):
        print('listening')
        while True:
            for event in self.filter.get_new_entries():
                try:
                    if (event.transactionHash.hex() == self.lasttxn):
                        return
                    self.lasttxn = event.transactionHash.hex()
                    print(event.transactionHash.hex())
                    await self.updateBalance()
                except Exception as e: 
                    print(e)
            await asyncio.sleep(10)

def dealwithbalance(pool_,token0,token1,swap):
    pool_.token0_bal = token0 / 10**pool_.token0_decimal
    pool_.token1_bal = token1 / 10**pool_.token1_decimal
    total = pool_.token0_bal + pool_.token1_bal
    pool_.token0_per = round(pool_.token0_bal / total * 100, 2)
    pool_.token1_per = round(pool_.token1_bal / total * 100, 2)
    pool_.ratio = [pool_.token0_per,pool_.token1_per]
    pool_.swap_price = swap / 10**(pool_.token1_decimal)
    print(pool_.token0_bal)
    print(pool_.token1_bal)
    print(pool_.pool_name)

def listening():
    while True:
        multi = Multicall([
            Call(three_pool.contract_addy,['balances(uint256)(uint256)', 0],[['three_pooltoken0',None]]),
            Call(three_pool.contract_addy,['balances(uint256)(uint256)', 1],[['three_pooltoken1',None]]),
            Call(three_pool.contract_addy,['balances(uint256)(uint256)', 2],[['three_pooltoken2',None]]),
            Call(frax_pool.contract_addy,['balances(uint256)(uint256)', 0],[['FRAXtoken0',None]]),
            Call(frax_pool.contract_addy,['balances(uint256)(uint256)', 1],[['FRAXtoken1',None]]),
            Call(frax_pool.contract_addy,['get_dy(int128,int128,uint256)(uint256)',0,1,int((10**(frax_pool.token0_decimal)))],[['FRAXtokenswap',None]]),
            Call(steth_pool.contract_addy,['balances(uint256)(uint256)', 0],[['STETHtoken0',None]]),
            Call(steth_pool.contract_addy,['balances(uint256)(uint256)', 1],[['STETHtoken1',None]]),
            Call(steth_pool.contract_addy,['get_dy(int128,int128,uint256)(uint256)',0,1,int((10**(steth_pool.token0_decimal)))],[['STETHtokenswap',None]]),
            Call(usdd_pool.contract_addy,['balances(uint256)(uint256)', 0],[['USDDtoken0',None]]),
            Call(usdd_pool.contract_addy,['balances(uint256)(uint256)', 1],[['USDDtoken1',None]]),
            Call(usdd_pool.contract_addy,['get_dy(int128,int128,uint256)(uint256)',0,1,int((10**(usdd_pool.token0_decimal)))],[['USDDtokenswap',None]]),
            Call(cvxCRV_pool.contract_addy,['balances(uint256)(uint256)', 0],[['CVXCRVtoken0',None]]),
            Call(cvxCRV_pool.contract_addy,['balances(uint256)(uint256)', 1],[['CVXCRVtoken1',None]]),
            Call(cvxCRV_pool.contract_addy,['get_dy(int128,int128,uint256)(uint256)',0,1,int((10**(cvxCRV_pool.token0_decimal)))],[['CVXCRVtokenswap',None]]),
            Call(lusd_pool.contract_addy,['balances(uint256)(uint256)', 0],[['LUSDtoken0',None]]),
            Call(lusd_pool.contract_addy,['balances(uint256)(uint256)', 1],[['LUSDtoken1',None]]),
            Call(lusd_pool.contract_addy,['get_dy(int128,int128,uint256)(uint256)',0,1,int((10**(lusd_pool.token0_decimal)))],[['LUSDtokenswap',None]]),
            Call(mim_pool.contract_addy,['balances(uint256)(uint256)', 0],[['MIMtoken0',None]]),
            Call(mim_pool.contract_addy,['balances(uint256)(uint256)', 1],[['MIMtoken1',None]]),
            Call(mim_pool.contract_addy,['get_dy(int128,int128,uint256)(uint256)',0,1,int((10**(mim_pool.token0_decimal)))],[['MIMtokenswap',None]]),
            Call(renBTC_pool.contract_addy,['balances(int128)(uint256)', 0],[['RENBTCtoken0',None]]),
            Call(renBTC_pool.contract_addy,['balances(int128)(uint256)', 1],[['RENBTCtoken1',None]]),
            Call(renBTC_pool.contract_addy,['get_dy(int128,int128,uint256)(uint256)',0,1,int((10**(renBTC_pool.token0_decimal)))],[['RENBTCtokenswap',None]]),
            Call(frax_bp.contract_addy,['balances(uint256)(uint256)', 0],[['FRAXBPtoken0',None]]),
            Call(frax_bp.contract_addy,['balances(uint256)(uint256)', 1],[['FRAXBPtoken1',None]]),
            Call(frax_bp.contract_addy,['get_dy(int128,int128,uint256)(uint256)',0,1,int((10**(frax_bp.token0_decimal)))],[['FRAXBPtokenswap',None]])
            ], _w3 = w3)
        data = multi()
        three_pool.token0_bal = data['three_pooltoken0'] / 10**three_pool.token0_decimal
        three_pool.token1_bal = data['three_pooltoken1'] / 10**three_pool.token1_decimal
        three_pool.token2_bal = data['three_pooltoken2'] / 10**three_pool.token2_decimal
        total = three_pool.token0_bal + three_pool.token1_bal + three_pool.token2_bal
        three_pool.virtual_price = three_pool.contract.caller.get_virtual_price() / 10**18
        three_pool.token0_per = round(three_pool.token0_bal / total * 100, 2)
        three_pool.token1_per = round(three_pool.token1_bal / total * 100, 2)
        three_pool.token2_per = round(three_pool.token2_bal / total * 100, 2)
        three_pool.ratio = [three_pool.token0_per,three_pool.token1_per,three_pool.token2_per]
        print(three_pool.token0_bal)
        print(three_pool.token1_bal)
        print(three_pool.token2_bal)
        print(three_pool.pool_name)
        dealwithbalance(frax_pool, data['FRAXtoken0'], data['FRAXtoken1'], data['FRAXtokenswap'])
        dealwithbalance(steth_pool, data['STETHtoken0'], data['STETHtoken1'], data['STETHtokenswap'])
        dealwithbalance(usdd_pool, data['USDDtoken0'], data['USDDtoken1'], data['USDDtokenswap'])
        dealwithbalance(cvxCRV_pool, data['CVXCRVtoken0'], data['CVXCRVtoken1'], data['CVXCRVtokenswap'])
        dealwithbalance(lusd_pool, data['LUSDtoken0'], data['LUSDtoken1'], data['LUSDtokenswap'])
        dealwithbalance(mim_pool, data['MIMtoken0'], data['MIMtoken1'], data['MIMtokenswap'])
        dealwithbalance(renBTC_pool, data['RENBTCtoken0'], data['RENBTCtoken1'], data['RENBTCtokenswap'])
        dealwithbalance(frax_bp, data['FRAXBPtoken0'], data['FRAXBPtoken1'], data['FRAXBPtokenswap'])
        try:
            gno_pool.token0_bal = gno_pool.contract.caller.balances(0) / 10**gno_pool.token0_decimal
            gno_pool.token1_bal = gno_pool.contract.caller.balances(1) / 10**gno_pool.token1_decimal
            gno_pool.token2_bal = gno_pool.contract.caller.balances(2) / 10**gno_pool.token2_decimal
            total = gno_pool.token0_bal + gno_pool.token1_bal + gno_pool.token2_bal
            gno_pool.token0_per = round(gno_pool.token0_bal / total * 100, 2)
            gno_pool.token1_per = round(gno_pool.token1_bal / total * 100, 2)
            gno_pool.token2_per = round(gno_pool.token2_bal / total * 100, 2)
            gno_pool.ratio = [gno_pool.token0_per,gno_pool.token1_per,gno_pool.token2_per]
            print(gno_pool.token0_bal)
            print(gno_pool.token1_bal)
            print(gno_pool.token2_bal)
        except:
            logging.error('error with gno')
        print('listen')
        logging.error('listening')
        time.sleep(10)

async def update_balance(context: ContextTypes):
    await asyncio.gather(three_pool .updateBalance(),
        gno_pool.updateBalance(),
        frax_pool.updateBalance(),
        steth_pool.updateBalance(),
        usdd_pool.updateBalance(),
        renBTC_pool.updateBalance(),
        cvxCRV_pool.updateBalance(),
        lusd_pool.updateBalance(),
        mim_pool.updateBalance(),
        frax_bp.updateBalance())
    print('checking for alerts to trigger')
    logging.error('checking alerts')

async def reserves(update: Update, context: ContextTypes):
    print(update.message.text.split(" ")[1:])
    try:
        texts = (update.message.text.split(" ")[1:])
        message = []
        if (texts == []):
            message = [
            f'DAI: {three_pool.token0_bal:,} ({three_pool.ratio[0]}%)\nUSDC: {three_pool.token1_bal:,} ({three_pool.ratio[1]}%)\nUSDT: {three_pool.token2_bal:,} ({three_pool.ratio[2]}%)\n\ngnoDAI: {gno_pool.token0_bal:,} ({gno_pool.ratio[0]}%)\ngnoUSDC: {gno_pool.token1_bal:,} ({gno_pool.ratio[1]}%)\ngnoUSDT: {gno_pool.token2_bal:,} ({gno_pool.ratio[2]}%)'
            ]
            for pool_ in current_pools:
                if (pool_.token1 == '3Crv'): 
                    message.append(f'{pool_.token0}: {pool_.token0_bal:,} ({pool_.ratio[0]}%)\n{pool_.token1}: {pool_.token1_bal:,} ({pool_.ratio[1]}%)\n1 {pool_.token0} -> {pool_.swap_price} {pool_.token1}/{pool_.swap_price * three_pool.virtual_price} USD')
                else: 
                    message.append(
                        f'{pool_.token0}: {pool_.token0_bal:,} ({pool_.ratio[0]}%)\n{pool_.token1}: {pool_.token1_bal:,} ({pool_.ratio[1]}%)\n1 {pool_.token0} -> {pool_.swap_price} {pool_.token1}'
                    )
            return await update.message.reply_text(
                '\n\n'.join(message)
            )
        for text in texts:
            text = text.lower()
            if (text == '3pool'):
                message.append( 
                    f'DAI: {three_pool.token0_bal:,} ({three_pool.ratio[0]}%)\nUSDC: {three_pool.token1_bal:,} ({three_pool.ratio[1]}%)\nUSDT: {three_pool.token2_bal:,} ({three_pool.ratio[2]}%)\n\ngnoDAI: {gno_pool.token0_bal:,} ({gno_pool.ratio[0]}%)\ngnoUSDC: {gno_pool.token1_bal:,} ({gno_pool.ratio[1]}%)\ngnoUSDT: {gno_pool.token2_bal:,} ({gno_pool.ratio[2]}%)'
                )
            elif (text == 'gnopool'):
                message.append( 
                    f'gnoDAI: {gno_pool.token0_bal:,} ({gno_pool.ratio[0]}%)\ngnoUSDC: {gno_pool.token1_bal:,} ({gno_pool.ratio[1]}%)\ngnoUSDT: {gno_pool.token2_bal:,} ({gno_pool.ratio[2]}%)'
            )   
            else:
                for pool_ in current_pools:
                    if (text == pool_.pool_name):
                        if (pool_.token1 == '3Crv'):
                            message.append(
                                f'{pool_.token0}: {pool_.token0_bal:,} ({pool_.ratio[0]}%)\n{pool_.token1}: {pool_.token1_bal:,} ({pool_.ratio[1]}%)\n1 {pool_.token0} -> {pool_.swap_price} {pool_.token1}/{pool_.swap_price * three_pool.virtual_price} USD'
                            )
                        else:
                            message.append(
                                f'{pool_.token0}: {pool_.token0_bal:,} ({pool_.ratio[0]}%)\n{pool_.token1}: {pool_.token1_bal:,} ({pool_.ratio[1]}%)\n1 {pool_.token0} -> {pool_.swap_price} {pool_.token1}'
                            )
            if text == (texts[-1]).lower() and message != []:
                return await update.message.reply_text('\n\n'.join(message))

        for pool_ in current_pools:
            message.append(pool_.pool_name)
        return await update.message.reply_text(
            'Sorry, not recognized\nCurrent recognized pools are:\n3pool\ngnopool\n' + '\n'.join(message)
        )
    except:
        return await update.message.reply_text('Error')

async def addalert(update: Update, context: ContextTypes):
    chat_id=update.effective_chat.id
    print(chat_id)
    try:
        text = (update.message.text.split(" ")[1]).split(",")
        if len(text) > 4:
            print('Error - too many variables')
            return update.message.reply_text('Error - too many variables')
        if (text[0].lower() == '3pool'):
            if ((text[1] == '0' and text[2] == '0' ) or (text[1] == '0' and text[3] == '0') or (text[2] == '0' and text[3] == '0')):
                sql.add3poolAlert('3pool', chat_id, text[1], text[2], text[3])
                return await update.message.reply_text('3pool alert added!')
            else:
                return await update.message.reply_text('Error, 2 of the token balance must be 0!')
        elif (text[0].lower() == 'gnopool'):
            if ((text[1] == '0' and text[2] == '0' ) or (text[1] == '0' and text[3] == '0') or (text[2] == '0' and text[3] == '0')):
                sql.add3poolAlert('gnopool', chat_id, text[1], text[2], text[3])
                return await update.message.reply_text('gnopool alert added!')
            else:
                return await update.message.reply_text('Error, 2 of the token balance must be 0!')
        else:
            for pool_ in current_pools:
                print(text)
                if (text[0].lower() == pool_.pool_name):
                    if ((text[1] == '0') or (text[2] == '0')):
                        sql.addAlert(text[0].lower(), chat_id, text[1], text[2])
                        return await update.message.reply_text(f'{text[0].lower()} alert added!')
                    else:
                        return await update.message.reply_text('Error, 1 of the token balance must be 0!')
        return await update.message.reply_text('Error, No such pool!')
    except:
        return await update.message.reply_text('Error!!')
    
async def removealert(update: Update, context: ContextTypes):
    chat_id = update.effective_chat.id
    print(chat_id)
    try:
        text = (update.message.text.split(" ")[1])
        text = text.lower()
        if (text == '3pool'):
            sql.remove3poolAlert('3pool',chat_id)
            return await update.message.reply_text('All 3pool alerts removed')
        elif (text == 'gnopool'):
            sql.remove3poolAlert('gnopool',chat_id)
            return await update.message.reply_text('All gnopool alerts removed')
        else:
            sql.removeAlert(text,chat_id)
            return await update.message.reply_text(f'All {text} alerts removed')
    except:
        return await update.message.reply_text('Error')

async def getalert(update: Update, context: ContextTypes):
    chat_id = update.effective_chat.id
    print(chat_id)
    try:
        text = (update.message.text.split(" ")[1])
        text = text.lower()
        if (text == '3pool'):
            message = ['Your 3pool alerts are:']
            rows = sql.get3poolAlerts('3pool')
            for row in rows:
                if row[2] == str(chat_id):
                    message.append(f'DAI:{row[3]}% USDC:{row[4]}% USDT:{row[5]}%')
            await update.message.reply_text('\n'.join(message))
        elif (text == 'gnopool'):
            message = ['Your gnopool alerts are:']
            rows = sql.get3poolAlerts('gnopool')
            for row in rows:
                if row[2] == str(chat_id):
                    message.append(f'DAI:{row[3]}% USDC:{row[4]}% USDT:{row[5]}%')
            await update.message.reply_text('\n'.join(message))
        else:
            for pool_ in current_pools:
                if (text == pool_.pool_name):
                    message = [f'Your {text} alerts are:']
                    rows = sql.getAlerts(text)
                    for row in rows:
                        if row[2] == str(chat_id):
                            message.append(f'{pool_.token0}:{row[3]}% {pool_.token1}:{row[4]}%')
                    return await update.message.reply_text('\n'.join(message))
            await update.message.reply_text('Error, No such pool!')
    except:
        return await update.message.reply_text('Error')

async def ensure_thread(context: ContextTypes):
    global t1
    print('ensure')
    print(t1)
    print(t1.is_alive())
    logging.error(f'thread is {t1.is_alive()}')
    if t1.is_alive() == False:
        t1 = Thread(target = listening)
        t1.start()
        logging.error(f'thread restarted')

def main() -> None:
    global three_pool
    global gno_pool
    global frax_pool
    global steth_pool
    global usdd_pool
    global renBTC_pool
    global cvxCRV_pool
    global lusd_pool
    global mim_pool
    global frax_bp
    three_pool = threepool('3pool', '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7', 'eth')
    gno_pool = threepool('gnopool', '0x7f90122BF0700F9E7e1F688fe926940E8839F353', 'gno')
    frax_pool = pool('frax','0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B')
    steth_pool = pool('steth','0xDC24316b9AE028F1497c275EB9192a3Ea0f67022')
    usdd_pool = pool('usdd','0xe6b5CC1B4b47305c58392CE3D359B10282FC36Ea')
    renBTC_pool = pool('renBTC', '0x93054188d876f558f4a66B2EF1d97d16eDf0895B')
    cvxCRV_pool = pool('cvxCRV', '0x9D0464996170c6B9e75eED71c68B99dDEDf279e8')
    lusd_pool = pool('LUSD', '0xEd279fDD11cA84bEef15AF5D39BB4d4bEE23F0cA')
    mim_pool = pool('MIM', '0x5a6A4D54456819380173272A5E8E9B9904BdF41B')
    frax_bp = pool('FRAXBP', '0xDcEF968d416a41Cdac0ED8702fAC8128A64241A2')
    print('Pools all initialized')
    global current_pools
    current_pools = [frax_pool,usdd_pool,steth_pool,renBTC_pool,cvxCRV_pool,lusd_pool,mim_pool,frax_bp]

    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_KEY).build()
    job_queue = application.job_queue
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("reserves", reserves))
    application.add_handler(CommandHandler("addalert", addalert))
    application.add_handler(CommandHandler("removealert", removealert))
    application.add_handler(CommandHandler("getalert", getalert))
    global t1
    t1 = Thread(target = listening)
    t1.start()
    print(t1.is_alive())
    job_queue.run_repeating(update_balance,10)
    job_queue.run_repeating(ensure_thread,10)
    global bot 
    bot = application.bot
    # Run the bot until the user presses Ctrl-C
    application.run_polling(1)


if __name__ == '__main__':    
    main()