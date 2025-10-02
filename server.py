import argparse
import asyncio
import platform

import uvicorn

from app.config import get_config

port = int(get_config("server.port", 5000))
host = get_config("server.host", "0.0.0.0")
ssl_on = int(get_config("server.ssl_on", 0)) == 1
ssl_certfile = get_config("server.ssl_certfile", 0)
ssl_keyfile = get_config("server.ssl_keyfile", 0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default=host)
    parser.add_argument("--port", type=int, default=port)
    parser.add_argument("--debug", action="store_true")
    args, other_args = parser.parse_known_args()

    server_args = {
        "host": args.host,
        "port": args.port,
        "timeout_graceful_shutdown": 3,
        "reload": args.debug,
    }
    if ssl_on:
        server_args["ssl_keyfile"] = ssl_keyfile
        server_args["ssl_certfile"] = ssl_certfile

    # merge with other_args
    for index, arg in enumerate(other_args):
        if arg == "--debug":
            continue

        if arg.startswith("--"):
            key = arg[2:].replace("-", "_")
            value = True
            server_args[key] = value
        else:
            # previous arg is key
            if index > 0 and other_args[index - 1].startswith("--"):
                key = other_args[index - 1][2:].replace("-", "_")
                server_args[key] = arg

    # if "log_config" not in server_args:
    #     server_args["log_config"] = str(
    #         ROOT_PATH / "logging.prod.conf" if not args.debug else ROOT_PATH / "logging.dev.conf"
    #     )

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    uvicorn.run("app.main:server", **server_args)
