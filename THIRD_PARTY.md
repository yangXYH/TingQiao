# 第三方组件

听桥采用本地语音识别和可配置语言模型的流程。产品形式参考了 Meetily 的录音整理体验，当前程序独立实现，不依赖或分发 Meetily 程序。

本仓库不分发第三方 Python 包、运行环境或语音模型权重。安装时下载的依赖及模型遵循其各自许可证；请保留依赖附带的 LICENSE、NOTICE 和包元数据。

| 组件 | 用途 | 官方项目 |
| --- | --- | --- |
| SenseVoice / FunAudioLLM | 语音识别模型 | https://github.com/FunAudioLLM/SenseVoice |
| sherpa-onnx | 本地 ONNX 语音识别推理 | https://github.com/k2-fsa/sherpa-onnx |
| Silero VAD | 语音活动检测 | https://github.com/snakers4/silero-vad |
| faster-whisper | 音频解码与 VAD 工具 | https://github.com/SYSTRAN/faster-whisper |
| PyAV | 音频读取和解码 | https://github.com/PyAV-Org/PyAV |
| ONNX Runtime | 模型推理 | https://github.com/microsoft/onnxruntime |
| NumPy | 数值处理 | https://github.com/numpy/numpy |
| FastAPI | 本地 HTTP 服务 | https://github.com/fastapi/fastapi |
| Uvicorn | ASGI 服务运行 | https://github.com/encode/uvicorn |
| python-multipart | 上传文件解析 | https://github.com/Kludex/python-multipart |

SenseVoice 模型下载和运行说明见 [sherpa-onnx 官方文档](https://k2-fsa.github.io/sherpa/onnx/sense-voice/pretrained.html)。下载工具会保留模型包中的 `LICENSE`，请进一步阅读其指向的上游模型使用条款。听桥源码的 MIT License 不改变第三方模型或服务的许可范围。
