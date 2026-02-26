# glados_auto_checkin

自动签到脚本，用于 https://glados.cloud/console/checkin 的签到自动化。

请在发布仓库中不要提交你的 `config.json`（其中包含敏感 Cookie）。使用 `config.json.example` 作为模板，在本地创建 `config.json` 并填写你的 Cookie。

快速开始

1. 复制示例配置并编辑：

```bash
cp config.json.example config.json
# 编辑 config.json，填入你的 cookie（不要提交到仓库）
```

2. 安装依赖并运行：

```bash
python3 -m pip install -r requirements.txt
python3 auto_checkin.py -c config.json
```

定时运行

项目内包含 `run_checkin.sh`，示例 crontab：

```cron
5 0 * * * /path/to/glados_auto_checkin/run_checkin.sh >> /path/to/glados_auto_checkin/cron.log 2>&1
```

安全说明

- 切勿在公开仓库中提交包含 Cookie 的 `config.json`。
- 若要撤销 Cookie，请在网站退出登录或换用新会话。
