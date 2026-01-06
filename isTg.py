import aiohttp
import asyncio
import aiofiles
import time

INPUT_FILE = 'followers_ready.txt'
OUTPUT_FILE = 'valid_users.txt'
CONCURRENT_REQUESTS = 5

async def check_username(session, username):
    clean_username = username.replace('@', '').strip()
    if not clean_username:
        return None
        
    url = f"https://t.me/{clean_username}"
    
    try:
        async with session.get(url, timeout=10) as response:
            text = await response.text()
            
            if 'tgme_page_photo_image' in text:
                print(f"[+] Найден: {clean_username}")
                return clean_username
            else:
                print(f"[-] Пусто: {clean_username}")
                return None
                
    except Exception as e:
        print(f"[!] Ошибка {clean_username}: {e}")
        return None

async def worker(queue, session, file_handle):
    while True:
        username = await queue.get()
        valid_user = await check_username(session, username)
        
        if valid_user:
            await file_handle.write(f"@{valid_user}\n")
            await file_handle.flush()
            
        queue.task_done()
        await asyncio.sleep(0.5) 

async def main():
    queue = asyncio.Queue()
    
    try:
        async with aiofiles.open(INPUT_FILE, mode='r') as f:
            async for line in f:
                await queue.put(line)
    except FileNotFoundError:
        print(f"Файл {INPUT_FILE} не найден!")
        return

    print(f"Загружено {queue.qsize()} ников. Начинаем проверку...")
    
    async with aiofiles.open(OUTPUT_FILE, mode='w') as out_file:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(CONCURRENT_REQUESTS):
                task = asyncio.create_task(worker(queue, session, out_file))
                tasks.append(task)
            
            await queue.join()
            
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    print(f"Готово! Результаты сохранены в {OUTPUT_FILE}")

if __name__ == '__main__':
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())