import asyncio

async def my_async_function_1():
    print("Running async function")
    await asyncio.sleep(3)

async def my_async_function_2():
    print("Finished async function")
    await asyncio.sleep(1)


async def main():
    await my_async_function_1()
    await my_async_function_2()
    # This runs the function and waits for it to complete

asyncio.run(main())

async def main():
    # Run both async functions concurrently
    await asyncio.gather(
        my_async_function_1(),
        my_async_function_2()
    )
asyncio.run(main())