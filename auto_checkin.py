#!/usr/bin/env python3
"""
Same as top-level `auto_checkin.py`. This copy is prepared for release packaging.
"""
import argparse
import json
import logging
import os
import re
import sys
from typing import Optional

import requests

LOG = logging.getLogger("glados_auto_checkin")


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def requests_checkin(config: dict) -> int:
    cookie = config.get("cookie")
    if not cookie:
        LOG.error("requests 模式需要在配置中提供 'cookie' 字段")
        return 0

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    session.headers.update({"Cookie": cookie})

    checkin_page = config.get("checkin_page", "https://glados.cloud/console/checkin")
    LOG.info("请求签到页面：%s", checkin_page)
    r = session.get(checkin_page, timeout=15)
    if r.status_code != 200:
        LOG.error("获取签到页面失败：%s", r.status_code)
        return r.status_code

    token = None
    m = re.search(r"name=[\"'](csrf_token|_token)[\"']\s+value=[\"']([^\"']+)[\"']", r.text)
    if m:
        token = m.group(2)
        LOG.debug("发现 csrf token：%s", token)

    post_url = config.get("checkin_post_url")
    if not post_url:
        post_url = checkin_page

    data = config.get("post_data", {})
    post_json = config.get("post_json")
    if token:
        if "csrf_token" in data or "_token" in data:
            pass
        else:
            data.setdefault("_token", token)

    if post_json is not None:
        LOG.info("提交签到请求到 %s，JSON body 字段：%s", post_url, list(post_json.keys()) if isinstance(post_json, dict) else type(post_json))
        resp = session.post(post_url, json=post_json, timeout=15)
    else:
        LOG.info("提交签到请求到 %s，表单字段：%s", post_url, list(data.keys()))
        resp = session.post(post_url, data=data, timeout=15)

    try:
        LOG.info("签到返回：%s %s", resp.status_code, resp.text[:300])
    except Exception:
        LOG.info("签到返回：%s (无法显示文本)", resp.status_code)
    return resp.status_code


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", default="config.json", help="配置文件路径（JSON）")
    parser.add_argument("--mode", "-m", choices=["requests"], default=None, help="强制使用的模式")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format="%(levelname)s: %(message)s")

    if not os.path.exists(args.config):
        LOG.error("配置文件不存在：%s", args.config)
        sys.exit(2)

    config = load_config(args.config)

    mode = args.mode or config.get("mode", "requests")

    if mode == "requests":
        code = requests_checkin(config)
        if code and code < 400:
            LOG.info("请求模式签到看起来成功（HTTP %s）", code)
            sys.exit(0)
        else:
            LOG.error("请求模式签到失败或未确认（HTTP %s）", code)
            sys.exit(1)


if __name__ == "__main__":
    main()
