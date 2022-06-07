import asyncio
async def greet_every_two_seconds():
     while True:
         print('Hello World')
         await asyncio.sleep(2)

 # run in main thread (Ctrl+C to cancel)
loop = asyncio.get_event_loop()
asyncio.create_task(greet_every_two_seconds())
