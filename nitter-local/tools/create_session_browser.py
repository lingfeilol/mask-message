#!/usr/bin/env python3
"""
Requirements: pip install -r tools/requirements.txt  (nodriver, pyotp)

Usage:
  python3 create_session_browser.py <用户名> <密码> [TOTP密钥] [--append ../sessions.jsonl] [--headless]

Examples:
  # 输出到终端
  python3 create_session_browser.py myusername mypassword TOTP_SECRET

  # 追加到 sessions.jsonl（推荐：直接写到上级目录）
  python3 create_session_browser.py myusername mypassword TOTP_SECRET --append ../sessions.jsonl

  # 无头模式（可能更容易被风控）
  python3 create_session_browser.py myusername mypassword TOTP_SECRET --headless

Output: 一行 JSON，或追加到指定文件。
"""

import sys
import json
import asyncio
import os

try:
    import pyotp
except ImportError:
    print("请先安装: pip install pyotp", file=sys.stderr)
    sys.exit(1)
try:
    import nodriver as uc
except ImportError:
    print("请先安装: pip install nodriver", file=sys.stderr)
    sys.exit(1)


async def login_and_get_cookies(username, password, totp_seed=None, headless=False):
    """用浏览器登录 x.com 并取出 session cookies"""
    browser = await uc.start(headless=headless)
    tab = await browser.get("https://x.com/i/flow/login")

    try:
        print("[*] 输入用户名...", file=sys.stderr)
        username_input = await tab.find("input[autocomplete=\"username\"]", timeout=10)
        await username_input.send_keys(username + "\n")
        await asyncio.sleep(1)

        print("[*] 输入密码...", file=sys.stderr)
        password_input = await tab.find("input[autocomplete=\"current-password\"]", timeout=15)
        await password_input.send_keys(password + "\n")
        await asyncio.sleep(2)

        page_content = await tab.get_content()
        if "verification code" in page_content or "Enter code" in page_content:
            if not totp_seed:
                raise Exception("检测到 2FA，但未提供 TOTP 密钥")
            print("[*] 检测到 2FA，输入验证码...", file=sys.stderr)
            totp_code = pyotp.TOTP(totp_seed).now()
            code_input = await tab.find("input[type=\"text\"]", timeout=5)
            await code_input.send_keys(totp_code + "\n")
            await asyncio.sleep(3)

        print("[*] 获取 Cookie...", file=sys.stderr)
        for _ in range(20):
            cookies = await browser.cookies.get_all()
            cookies_dict = {cookie.name: cookie.value for cookie in cookies}

            if "auth_token" in cookies_dict and "ct0" in cookies_dict:
                print("[*] 已获取 auth_token 和 ct0", file=sys.stderr)
                user_id = None
                if "twid" in cookies_dict:
                    twid = cookies_dict["twid"]
                    if "u%3D" in twid:
                        user_id = twid.split("u%3D")[1].split("&")[0].strip('"')
                    elif "u=" in twid:
                        user_id = twid.split("u=")[1].split("&")[0].strip('"')
                cookies_dict["username"] = username
                if user_id:
                    cookies_dict["id"] = user_id
                return cookies_dict

            await asyncio.sleep(1)

        raise Exception("等待 Cookie 超时")

    finally:
        browser.stop()


async def main():
    if len(sys.argv) < 3:
        print("用法: python3 create_session_browser.py <用户名> <密码> [TOTP密钥] [--append sessions.jsonl] [--headless]", file=sys.stderr)
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    totp_seed = None
    append_file = None
    headless = False

    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--append":
            if i + 1 < len(sys.argv):
                append_file = sys.argv[i + 1]
                i += 2
            else:
                print("[!] --append 需要指定文件名", file=sys.stderr)
                sys.exit(1)
        elif arg == "--headless":
            headless = True
            i += 1
        elif not arg.startswith("--"):
            if totp_seed is None:
                totp_seed = arg
            i += 1
        else:
            print(f"[!] 未知参数: {arg}", file=sys.stderr)
            i += 1

    try:
        cookies = await login_and_get_cookies(username, password, totp_seed, headless)
        session = {
            "kind": "cookie",
            "username": cookies["username"],
            "id": cookies.get("id"),
            "auth_token": cookies["auth_token"],
            "ct0": cookies["ct0"],
        }
        output = json.dumps(session)

        if append_file:
            with open(append_file, "a", encoding="utf-8") as f:
                f.write(output + "\n")
            print(f"✓ 已追加到 {append_file}", file=sys.stderr)
        else:
            print(output)

        os._exit(0)

    except Exception as error:
        print(f"[!] 错误: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
