import asyncio
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn  # noqa: E402

async def main():
    config = uvicorn.Config('api.main:app', host='127.0.0.1', port=8000, log_level='info')
    server = uvicorn.Server(config)
    serve_task = asyncio.create_task(server.serve())
    await asyncio.sleep(3)
    server.should_exit = True
    await serve_task

if __name__ == '__main__':
    asyncio.run(main())
