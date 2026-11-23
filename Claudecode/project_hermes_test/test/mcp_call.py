"""llmwiki 로컬 MCP 서버의 도구 하나를 stdio로 호출한다(테스트용).

Hermes 대신 Claude Code 하위 에이전트가 Bash로 llmwiki를 쓰게 하려고 만든 얇은 클라이언트다.
현재 세션에 MCP를 새로 등록하면 재시작 전까지 하위 에이전트가 도구를 못 받기 때문이다.

사용:
  python mcp_call.py --list                     도구 이름과 입력 스키마 출력
  python mcp_call.py <tool> '<json 인자>'         도구 호출, 텍스트 결과 출력
  python mcp_call.py <tool> @args.json          인자를 파일에서 읽기(긴 본문용)

환경변수: LLMWIKI_PY(venv python), LLMWIKI_APP(llmwiki 루트), LLMWIKI_WS(워크스페이스)
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HOME = Path(os.environ["USERPROFILE"] if os.name == "nt" else os.environ["HOME"])
APP = Path(os.environ.get("LLMWIKI_APP", HOME / "llmwiki-local" / "app"))
PY = os.environ.get("LLMWIKI_PY", str(APP / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")))
WS = os.environ.get("LLMWIKI_WS", str(HOME / "llmwiki-local" / "wiki"))


def _load_args(raw: str) -> dict:
    if raw.startswith("@"):
        return json.loads(Path(raw[1:]).read_text(encoding="utf-8"))
    return json.loads(raw)


async def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    params = StdioServerParameters(
        command=PY,
        args=[str(APP / "mcp" / "local_server.py"), WS],
        cwd=str(APP / "mcp"),
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )
    async with stdio_client(params, errlog=open(os.devnull, "w")) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            if sys.argv[1] == "--list":
                for t in (await s.list_tools()).tools:
                    print(f"## {t.name}\n{t.description}\n{json.dumps(t.inputSchema.get('properties', {}), ensure_ascii=False)}\n")
                return 0
            args = _load_args(sys.argv[2]) if len(sys.argv) > 2 else {}
            res = await s.call_tool(sys.argv[1], args)
            for c in res.content:
                print(getattr(c, "text", c))
            return 1 if res.isError else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(asyncio.run(main()))
