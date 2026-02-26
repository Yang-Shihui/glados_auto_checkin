# glados_auto_checkin

这是一个glados的自动签到工具，针对 https://glados.cloud/console/checkin 页面实现自动签到

功能概述
- 模拟 HTTP 请求完成签到流程（基于用户提供的 Cookie）。
- 可作为服务器上的定时任务（cron）运行，实现每日自动签到。

先决条件
- Python 3.8 或更高
- pip 可用于安装依赖

安装
```bash
# 进入 release 目录或将 release 下的文件复制到目标目录
cd glados_auto_checkin
pip install -r requirements.txt
```

配置
1. 复制示例配置并编辑：

```bash
cp config.json.example config.json
# 然后用编辑器打开 config.json，填写你的 cookie 字段
```

2. `config.json` 常用字段说明：
- `mode`: 当前 release 仅支持 `requests`。
- `checkin_page`: 用于先访问获取页面上下文（通常无需更改）。
- `cookie`: 浏览器复制的 Cookie 字符串（整行），示例： `koa:sess=...; koa:sess.sig=...`。
- `checkin_post_url`: 签到 API 地址，示例 `https://glados.cloud/api/user/checkin`。
- `post_json`: POST 请求的 JSON body（示例 `{ "token": "glados.cloud" }`）。

本地运行示例
```bash
python auto_checkin.py -c config.json
# 调试模式：
python auto_checkin.py -c config.json --debug
```

定时运行（可选）

仓库中已包含 `run_checkin.sh`，会把输出追加到 `daily_checkin.log`。要让系统每天自动运行，可把下面的 crontab 行添加到当前用户的 crontab（示例：每天 00:05）：

```cron
5 0 * * * /path/to/glados_auto_checkin/run_checkin.sh >> /path/to/glados_auto_checkin/cron.log 2>&1
```

排错指导
- 若脚本运行失败，使用 `--debug` 获取更多日志信息。
- cron 环境与交互式 shell 不同：请确保 `run_checkin.sh` 中使用的路径是绝对路径或基于脚本位置；并确保脚本有可执行权限（`chmod +x run_checkin.sh`）。
- 查看日志：
	- 脚本日志： `tail -n 200 /path/to/glados_auto_checkin/daily_checkin.log`
	- cron 输出： `tail -n 200 /path/to/glados_auto_checkin/cron.log`

扩展说明
扩展说明
- 支持三种模式：`requests`、`selenium`、`playwright`。

浏览器模式说明（可选）
- `selenium` 模式：需要 `selenium` Python 包以及对应浏览器驱动（chromedriver 或 geckodriver）。示例安装：

```bash
python -m pip install selenium
# 下载 chromedriver 并放在 PATH 中，或使用系统包管理器安装
```

- `playwright` 模式：需要 `playwright` 包并下载 Playwright 浏览器：

```bash
python -m pip install playwright
python -m playwright install
```

开启浏览器模式示例（使用 selenium）：

```bash
python auto_checkin.py -c config.json -m selenium
```

开启 Playwright 模式示例：

```bash
python auto_checkin.py -c config.json -m playwright
```

许可证
本项目以 MIT 许可证发布，见 `LICENSE` 文件。



