#!/usr/bin/env python3
"""
自动签到脚本（完整实现，含 requests/selenium/playwright 三种模式）。

使用方法和配置参见 README。
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

# 完整浏览器指纹，避免光秃秃的 "Mozilla/5.0" 显得像脚本
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def requests_checkin(config: dict) -> int:
    """使用 requests 尝试签到。需要 config 中至少包含 cookie 字符串。

    返回 HTTP 状态码或 0 表示未发送请求。
    """
    cookie = config.get("cookie")
    if not cookie:
        LOG.error("requests 模式需要在配置中提供 'cookie' 字段")
        return 0

    session = requests.Session()
    # 设置 cookie 与浏览器指纹
    session.headers.update({"User-Agent": BROWSER_UA,
                            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"})
    session.headers.update({"Cookie": cookie})

    checkin_page = config.get("checkin_page", "https://glados.cloud/console/checkin")
    LOG.info("请求签到页面：%s", checkin_page)
    r = session.get(checkin_page, timeout=15)
    if r.status_code != 200:
        LOG.error("获取签到页面失败：%s", r.status_code)
        return r.status_code

    # 尝试从页面中抓取 csrf token（常见字段名）
    token = None
    # 先查找 name="csrf_token" 或 name="_token"
    m = re.search(r"name=[\"'](csrf_token|_token)[\"']\s+value=[\"']([^\"']+)[\"']", r.text)
    if m:
        token = m.group(2)
        LOG.debug("发现 csrf token：%s", token)

    post_url = config.get("checkin_post_url")
    if not post_url:
        # 尝试猜测 POST 地址
        post_url = checkin_page

    data = config.get("post_data", {})
    post_json = config.get("post_json")
    if token:
        # 如果已有 token，尝试以常见字段名注入
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


def selenium_checkin(config: dict) -> int:
    """使用 Selenium 在浏览器中打开页面并点击“签到”按钮。

    需要用户已安装 selenium 与 chromedriver 或 geckodriver，并在配置中指定浏览器类型（chrome/firefox 可选）。
    返回 1 成功，0 失败。
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.firefox.options import Options as FxOptions
    except Exception as e:
        LOG.error("无法导入 selenium，请先安装：pip install selenium")
        LOG.debug(e)
        return 0

    browser = config.get("browser", "chrome")
    url = config.get("checkin_page", "https://glados.cloud/console/checkin")
    headless = bool(config.get("headless", True))

    driver = None
    try:
        if browser == "firefox":
            opts = FxOptions()
            if headless:
                opts.headless = True
            driver = webdriver.Firefox(options=opts)
        else:
            opts = ChromeOptions()
            if headless:
                opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(options=opts)

        LOG.info("打开页面：%s", url)
        driver.get(url)

        # 等待并查找按钮文本包含“签到”的元素
        # 尝试多种选择器
        btn = None
        try:
            btn = driver.find_element(By.XPATH, "//button[contains(., '签到') or contains(., 'Sign in')]")
        except Exception:
            pass

        if not btn:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, "button.btn, a.btn")
            except Exception:
                pass

        if not btn:
            LOG.error("未找到签到按钮，请在浏览器中检查选择器或改用 requests 模式并提供 post 地址/cookie")
            return 0

        LOG.info("点击签到按钮")
        btn.click()
        LOG.info("已点击，等待结果")
        # 简单等待
        import time
        time.sleep(2)
        return 1
    except Exception as e:
        LOG.exception("selenium 签到失败：%s", e)
        return 0
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def playwright_checkin(config: dict) -> int:
    """使用 Playwright 在无头浏览器中打开页面并点击“签到”按钮。

    需要安装 `playwright` 并运行 `playwright install`。返回 1 成功，0 失败。
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        LOG.error("无法导入 playwright，请先安装：pip install playwright 然后运行 playwright install 浏览器")
        return 0

    url = config.get("checkin_page", "https://glados.cloud/console/checkin")
    headless = bool(config.get("headless", True))
    cookie_header = config.get("cookie", "")

    # Parse cookie header into dict
    cookies = []
    if cookie_header:
        for pair in cookie_header.split(";"):
            pair = pair.strip()
            if not pair:
                continue
            if "=" not in pair:
                continue
            name, value = pair.split("=", 1)
            cookies.append({"name": name, "value": value, "domain": ".glados.cloud", "path": "/"})

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=headless)
            context = browser.new_context()
            if cookies:
                context.add_cookies(cookies)
            page = context.new_page()
            LOG.info("Playwright 打开页面：%s", url)
            page.goto(url, timeout=60000, wait_until='networkidle')

            # 尝试点击包含“签到”的按钮
            found = False
            try:
                btn = page.query_selector("button:has-text('签到')")
                if not btn:
                    btn = page.query_selector("button:has-text('Sign in')")
                if btn:
                    btn.click()
                    found = True
            except Exception:
                pass

            if not found:
                # 尝试更宽泛的选择器
                try:
                    el = page.query_selector("button")
                    if el:
                        el.click()
                        found = True
                except Exception:
                    pass

            if not found:
                LOG.error("Playwright: 未找到签到按钮")
                browser.close()
                return 0

            page.wait_for_timeout(2000)
            LOG.info("Playwright: 点击完成，获取页面标题：%s", page.title())
            browser.close()
            return 1
    except Exception as e:
        LOG.exception("Playwright 签到失败：%s", e)
        return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", default="config.json", help="配置文件路径（JSON）")
    parser.add_argument("--mode", "-m", choices=["requests", "selenium", "playwright"], default=None, help="强制使用的模式")
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
    else:
        if mode == "selenium":
            ok = selenium_checkin(config)
        else:
            ok = playwright_checkin(config)
        if ok:
            LOG.info("selenium 模式签到可能成功")
            sys.exit(0)
        else:
            LOG.error("selenium 模式签到失败")
            sys.exit(1)


if __name__ == "__main__":
    main()
