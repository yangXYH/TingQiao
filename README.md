# 听桥 · TingQiao

**让录音成为可回顾、可检索、可行动的记录。**

听桥是一款本地优先的录音转写与 AI 分析工具。拖入音频，即可自动转写、生成会议纪要或面试复盘，并归档保存。录音在本机转写，生成分析时仅将转写文字发送至你选择的模型服务。

这是面向 Windows 和 macOS 的源码版本，界面通过本机浏览器窗口运行。支持 Apple Silicon 和 Intel Mac；当前不包含 Linux 适配、录音采集或线上会议接入。

## 功能

- **拖入即处理**：上传 M4A、MP3、WAV、FLAC 等录音，自动转写、分析和归档。
- **三种整理方式**：会议纪要、面试复盘、内容梳理。
- **本地语音识别**：SenseVoice + sherpa-onnx，使用 CPU 完成转写，无需将原始音频交给云端识别服务。
- **自定义分析模型**：支持兼容 Chat Completions 的接口，可设置 Base URL、模型名、API 密钥和思考模式。
- **录音档案**：搜索标题、转写内容和分析；校对原文；回听、倍速播放；自动命名。
- **保留分析版本**：重新分析复用已有转写，成功后保留旧版结果。
- **复制和导出**：支持 Markdown、转写 TXT、JSON。分析正文不显示录音时间引用，转写仍保留时间定位。
- **黑色夜间模式**：首次跟随系统，手动切换后记住选择。

当前单个文件上限 1 GB，单段音频上限 4 小时。识别质量受录音清晰度、口音和专业术语影响，重要信息请结合原文校对。

## 从源码运行

支持 Windows 10/11、macOS 14 及以上版本，需要 64 位 Python 3.12。首次安装依赖和语音模型需要网络；配置好模型文件后，语音转写可离线运行。云端分析需要网络与用户自己的模型权限或额度。

### macOS

先安装 [Python 3.12](https://www.python.org/downloads/macos/)；使用 Homebrew 时也可运行 `brew install python@3.12`。Apple Silicon 请选择原生 arm64 Python，避免通过 Rosetta 混用 Intel 环境。

```bash
git clone https://github.com/yangXYH/TingQiao.git
cd TingQiao
bash setup.sh
./启动听桥.command
```

也可双击 `setup.command` 完成首次安装，再双击 `启动听桥.command` 启动。若通过 ZIP 下载后没有执行权限，在终端运行 `chmod +x setup.command 启动听桥.command`。

有 Chrome 或 Edge 时优先使用独立应用窗口；否则在默认浏览器（如 Safari）中打开。首次保存或读取 API 密钥时，macOS 可能提示授权 Python 访问登录钥匙串，请按需允许。密钥只存入系统钥匙串，配置文件仅保存随机引用。

若模型已手动放置，执行 `bash setup.sh --skip-model`。直接启动后端可使用 `.venv/bin/python app/server.py`，再打开 <http://127.0.0.1:19331>。当前提供源码启动方式，不包含签名、公证的 `.app` 或 `.dmg` 安装包。

### Windows

安装 Python 时勾选 Python Launcher，浏览器建议使用 Edge 或 Chrome。

```powershell
git clone https://github.com/yangXYH/TingQiao.git
cd TingQiao
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

安装脚本会创建 `.venv`、安装 `requirements.txt` 中的依赖，并下载 SenseVoice int8 模型。这里的执行策略设置仅作用于这一次 PowerShell 进程，不修改系统策略。

安装完成后，双击项目目录下的 **启动听桥.vbs**。

也可以在终端运行服务，然后访问 <http://127.0.0.1:19331>：

```powershell
.\.venv\Scripts\python.exe .\app\server.py
```

### 手动放置语音模型

如果自动下载失败，可参考 [sherpa-onnx 官方 SenseVoice 文档](https://k2-fsa.github.io/sherpa/onnx/sense-voice/pretrained.html)，下载以下 int8 模型包：

[sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17.tar.bz2](https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17.tar.bz2)

解压后将这三个文件放入对应目录，再运行 `setup.ps1 -SkipModel` 安装依赖：

```text
models/sensevoice/
  model.int8.onnx
  tokens.txt
  LICENSE
```

语音模型及 Python 运行环境不包含在 Git 仓库中。

## 首次使用

1. 打开「模型连接」，填写自己的 Base URL、模型名和 API 密钥，测试并保存。
2. 回到「开始分析」，选择整理方式和分析模型。
3. 拖入录音，或点击「选择录音」。可以离开当前页面，任务会在后台继续。
4. 在「录音档案」查看结果、校对原文、回听或导出。

默认提供火山方舟的公开接口地址和模型别名作为连接模板，**不附带密钥、账号或额度**。实际可用模型由你的服务商和套餐决定；也可以新增其他兼容接口。

每次分析成功后会根据内容自动更新档案标题，包括重新分析。手动校对转写后，可点击「重新分析」更新分析内容。关闭应用窗口不等于结束后台服务。

## 数据与隐私

所有应用数据位于项目目录下，默认不进入 Git：

| 位置 | 内容 |
| --- | --- |
| `data/models.json` | 模型连接信息，以及 Windows 加密密钥或 macOS 钥匙串引用 |
| `data/archive.sqlite3` | 录音档案、转写文字和分析历史 |
| `data/recordings/` | 原始音频、回放音频、转写和分析文件 |
| `data/recycle/` | 从档案移除的录音文件，需自行管理清理 |
| `data/browser/` | 本机应用浏览器配置 |
| `logs/` | 服务运行日志 |

- Windows 密钥通过 DPAPI 加密保存，通常仅同一 Windows 用户可解密；macOS 密钥存入登录钥匙串，配置中仅保留随机引用。配置文件仍属于私有数据，请勿公开。
- 在 Windows 和 Mac 之间迁移录音档案后，需要在目标电脑重新填写 API 密钥；不导出系统凭据。
- 使用云端分析时，转写文字与请求所需凭据会发送到你配置的服务商。请确认你有权处理和传输相应内容。
- 服务默认仅监听 `127.0.0.1:19331`，适合个人本机使用；当前不提供多用户登录或公网部署能力。
- 分享或开源时只分享源码，不要打包整个已使用的应用目录。详见 [SECURITY.md](SECURITY.md)。

## 技术构成

后端使用 Python、FastAPI、SQLite；前端使用原生 HTML/CSS/JavaScript，无需 Node.js 构建。SenseVoice 负责识别，faster-whisper 提供音频解码和 VAD 工具，语言模型通过兼容 Chat Completions 的接口接入。

```text
app/                    后端、桌面启动器与静态界面
scripts/download_model.py 公开语音模型下载工具
scripts/check_release.py 提交内容检查工具
requirements.txt        Python 依赖
setup.ps1               Windows 安装脚本
setup.sh / setup.command macOS 安装入口
启动听桥.vbs             Windows 启动入口
启动听桥.command         macOS 启动入口
```

## 开发与贡献

欢迎提交 Issue 和 Pull Request。提交前建议执行：

```powershell
git add <需要提交的源码文件>
python scripts/check_release.py
```

检查脚本会检查 **Git 暂存区**，阻止常见密钥、私有数据路径和大型运行文件进入提交。它只能作为辅助，提交前仍需检查文件列表与差异。

平台与凭据存储测试：`python -m unittest discover -s tests -v`。GitHub Actions 会在 Windows、Apple Silicon Mac 和 Intel Mac 上安装依赖并运行测试；不会使用维护者的录音或模型密钥。

## 许可证

听桥源码使用 [MIT License](LICENSE)。第三方依赖及语音模型遵循各自的许可证，MIT 许可不覆盖第三方模型权重。参见 [THIRD_PARTY.md](THIRD_PARTY.md)。
