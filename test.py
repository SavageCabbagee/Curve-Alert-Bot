
from web3 import Web3
import asyncio
from dotenv import dotenv_values

config = dotenv_values(".env")
RPC_KEY = config['RPC_API']

w3 = Web3(Web3.HTTPProvider(f'https://eth-mainnet.alchemyapi.io/v2/{RPC_KEY}'))

def handle_event(event):
    print(event)
    # and whatever

async def log_loop(event_filter, poll_interval):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
        await asyncio.sleep(poll_interval)

def main():
    block_filter = w3.eth.filter('latest')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(
                log_loop(block_filter, 2),
                log_loop(tx_filter, 2)))
        print('test')
    finally:
        loop.close()

if __name__ == '__main__':
    main()