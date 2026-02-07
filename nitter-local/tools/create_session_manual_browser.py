#!/usr/bin/env python3
"""
适合「用 Google 账号登录推特」的方式：脚本只负责打开登录页、等你手动登录后再抓 Cookie。
无需输入推特密码，在浏览器里点「用 Google 登录」完成即可。

Requirements: pip install nodriver

Usage:
  python3 create_session_manual_browser.py [--append sessions.jsonl]

流程：
  1. 会打开浏览器并进入 x.com 登录页
  2. 你在页面里用 Google（或任意方式）登录
  3. 登录成功后脚本自动检测到 Cookie 并写入 sessions.jsonl，然后退出
"""

import sys
import json
import asyncio
import os

try:
    import nodriver as uc
except ImportError:
    print("请先安装: pip install nodriver", file=sys.stderr)
    sys.exit(1)


async def wait_for_login_and_get_cookies(append_file=None):
    browser = await uc.start(headless=False)
    tab = await browser.get("https://x.com/i/flow/login")

    print("\n请在浏览器中完成登录（例如点击「使用 Google 登录」）。", file=sys.stderr)
    print("登录成功后脚本会自动抓取 Cookie 并退出。\n", file=sys.stderr)

    try:
        for _ in range(300):  # 最多等 300 秒
            await asyncio.sleep(1)
            cookies = await browser.cookies.get_all()
            cookies_dict = {c.name: c.value for c in cookies}

            if "auth_token" in cookies_dict and "ct0" in cookies_dict:
                print("[*] 已检测到登录成功，正在保存 Cookie...", file=sys.stderr)

                user_id = None
                if "twid" in cookies_dict:
                    twid = cookies_dict["twid"]
                    if "u%3D" in twid:
                        user_id = twid.split("u%3D")[1].split("&")[0].strip('"')
                    elif "u=" in twid:
                        user_id = twid.split("u=")[1].split("&")[0].strip('"')

                username = cookies_dict.get("screen_name") or cookies_dict.get("username") or ""

                session = {
                    "kind": "cookie",
                    "username": username,
                    "id": user_id,
                    "auth_token": cookies_dict["auth_token"],
                    "ct0": cookies_dict["ct0"],
                }
                output = json.dumps(session)

                if append_file:
                    with open(append_file, "a", encoding="utf-8") as f:
                        f.write(output + "\n")
                    print(f"✓ 已追加到 {append_file}", file=sys.stderr)
                else:
                    print(output)

                browser.stop()
                os._exit(0)

        print("[!] 超时：未检测到登录成功", file=sys.stderr)
        browser.stop()
        sys.exit(1)

    except Exception as e:
        print(f"[!] 错误: {e}", file=sys.stderr)
        browser.stop()
        sys.exit(1)


async def main():
    append_file = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--append" and i < len(sys.argv) - 1:
            append_file = sys.argv[i + 1]
            break

    await wait_for_login_and_get_cookies(append_file)


if __name__ == "__main__":
    asyncio.run(main())
