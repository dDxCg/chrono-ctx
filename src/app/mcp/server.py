import argparse

from mcp.server.fastmcp import FastMCP

parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, default="127.0.0.1", help='MPC host')
parser.add_argument('--port', type=int, default=8000, help='MPC port')
args = parser.parse_args()

mcp = FastMCP("chrono-ctx", host=args.host ,port=args.port)

@mcp.tool()
async def read_file(path: str):
    """Read file contents"""
    return {
        "status": "ok",
        "content": None,
        "version": None
    }

@mcp.tool()
async def write_file(path: str):
    return {
        "status": "ok"
    }

@mcp.tool()
async def create_file(path: str):
    return {
        "status": "ok"
    }

@mcp.tool()
async def delete_file(path: str):
    return {
        "status": "ok"
    }

@mcp.tool()
async def move_file(src: str, dst: str):
    return {
        "status": "ok"
    }


def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
