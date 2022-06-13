import sqlite as sql
import asyncio
from web3 import Web3

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext

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
        print(f'{self.pool_name} started' )

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
        print(self.pool_name)


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
        self.token0_bal = self.contract.caller.balances(0) / 10**self.token0_decimal
        self.token1_bal = self.contract.caller.balances(1) / 10**self.token1_decimal
        self.token2_bal = self.contract.caller.balances(2) / 10**self.token2_decimal
        total = self.token0_bal + self.token1_bal + self.token2_bal
        self.virtual_price = self.contract.caller.get_virtual_price() / 10**18
        token0_per = round(self.token0_bal / total * 100, 2)
        token1_per = round(self.token1_bal / total * 100, 2)
        token2_per = round(self.token2_bal / total * 100, 2)
        self.ratio = [token0_per,token1_per,token2_per]
        print(self.token0_bal)
        print(self.token1_bal)
        print(self.token2_bal)
        print(self.pool_name)

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

three_pool = threepool('3pool', '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7', 'eth')
gno_pool = threepool('gnopool', '0x7f90122BF0700F9E7e1F688fe926940E8839F353', 'gno')
frax_pool = pool('frax','0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B')
steth_pool = pool('steth','0xDC24316b9AE028F1497c275EB9192a3Ea0f67022')
usdd_pool = pool('usdd','0xe6b5CC1B4b47305c58392CE3D359B10282FC36Ea')
renBTC_pool = pool('renBTC', '0x93054188d876f558f4a66B2EF1d97d16eDf0895B')
cvxCRV_pool = pool('cvxCRV', '0x9D0464996170c6B9e75eED71c68B99dDEDf279e8')
lusd_pool = pool('LUSD', '0xEd279fDD11cA84bEef15AF5D39BB4d4bEE23F0cA')
mim_pool = pool('MIM', '0x5a6A4D54456819380173272A5E8E9B9904BdF41B')
print('Pools all initialized')

current_pools = [frax_pool,usdd_pool,steth_pool,renBTC_pool,cvxCRV_pool,lusd_pool,mim_pool]

async def start_listening(context: CallbackContext):
    asyncio.create_task(three_pool.updateBalance())
    asyncio.create_task(gno_pool.updateBalance())
    asyncio.create_task(frax_pool.updateBalance())
    asyncio.create_task(steth_pool.updateBalance())
    asyncio.create_task(usdd_pool.updateBalance())
    asyncio.create_task(renBTC_pool.updateBalance())
    asyncio.create_task(cvxCRV_pool.updateBalance())
    asyncio.create_task(lusd_pool.updateBalance())
    asyncio.create_task(mim_pool.updateBalance())

    asyncio.ensure_future(three_pool.listen())
    asyncio.ensure_future(gno_pool.listen())
    asyncio.ensure_future(frax_pool.listen())
    asyncio.ensure_future(steth_pool.listen())
    asyncio.ensure_future(usdd_pool.listen())
    asyncio.ensure_future(renBTC_pool.listen())
    asyncio.ensure_future(cvxCRV_pool.listen())
    asyncio.ensure_future(lusd_pool.listen())
    asyncio.ensure_future(mim_pool.listen())
    print('All started listening!')

async def reserves(update: Update, context: ContextTypes):
    print(update.message.text.split(" ")[1:])
    try:
        text = (update.message.text.split(" ")[1:][0])
        text = text.lower()
        if (text == '3pool'):
            return await update.message.reply_text( 
                f'DAI: {three_pool.token0_bal:,} ({three_pool.ratio[0]}%)\nUSDC: {three_pool.token1_bal:,} ({three_pool.ratio[1]}%)\nUSDT: {three_pool.token2_bal:,} ({three_pool.ratio[2]}%)\n\ngnoDAI: {gno_pool.token0_bal:,} ({gno_pool.ratio[0]}%)\ngnoUSDC: {gno_pool.token1_bal:,} ({gno_pool.ratio[1]}%)\ngnoUSDT: {gno_pool.token2_bal:,} ({gno_pool.ratio[2]}%)'
            )
        elif (text == 'gnopool'):
            return await update.message.reply_text( 
                f'gnoDAI: {gno_pool.token0_bal:,} ({gno_pool.ratio[0]}%)\ngnoUSDC: {gno_pool.token1_bal:,} ({gno_pool.ratio[1]}%)\ngnoUSDT: {gno_pool.token2_bal:,} ({gno_pool.ratio[2]}%)'
            )
        else:
            for pool_ in current_pools:
                if (text == pool_.pool_name):
                    if (pool_.token1 == '3Crv'):
                        return await update.message.reply_text(
                            f'{pool_.token0}: {pool_.token0_bal:,} ({pool_.ratio[0]}%)\n{pool_.token1}: {pool_.token1_bal:,} ({pool_.ratio[1]}%)\n1 {pool_.token0} -> {pool_.swap_price} {pool_.token1}/{pool_.swap_price * three_pool.virtual_price} USD'
                        )
                    else:
                        return await update.message.reply_text(
                            f'{pool_.token0}: {pool_.token0_bal:,} ({pool_.ratio[0]}%)\n{pool_.token1}: {pool_.token1_bal:,} ({pool_.ratio[1]}%)\n1 {pool_.token0} -> {pool_.swap_price} {pool_.token1}'
                        )
        message = []
        for pool_ in current_pools:
            message.append(pool_.pool_name)
        return await update.message.reply_text(
            'Sorry, not recognized\nCurrent recognized pools are:\n3pool\ngnopool\n' + '\n'.join(message)
        )
    except:
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
        await update.message.reply_text(
            '\n\n'.join(message)
        )


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_KEY).build()
    job_queue = application.job_queue
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("reserves", reserves))
    job_queue.run_once(start_listening,60)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(1)
    
main()