# 大模型日志输出工具说明

## 工具描述
这是一个基于OpenAI接口的大模型的交互日志工具
支持记录完整的请求/响应的提问词信息,也可以监控流程及性能指标，主要用于调试和研究各种AI软件等用途。

## 日志输出格式
日志采用JSON格式存储，示例如下：

```json
{
  "timestamp": "20251118-170523-456",
  "path": "/chat/completions",
  "prompt": "用户输入的原始提示文本",
  "response": "AI 助手返回的完整回复内容",
  "stream": false,
  "latency_sec": 0.234,
  "status_code": 200
}
```

## 环境构筑

### conda的方式
create_conda.bat执行

### 手动pip的方式
pip install -r requirements.txt

## 使用手册
以端口号8000为例，
服务启动后,访问localhost:8000既是访问

## 配置方面
llm_prompts_log_server.py

### OPENAI_URL的配置如下变量进行设定
VLLM_BACKEND_URL = "http://192.168.1.1:8000/"
本地模型和online支持模型均可支持

### 本LOG服务的端口号设定
PROXY_PORT = 8000

### LOG的输出目录(默认是工程的相对目录)
LOG_FILE_PATH = f"./Log/openai_log_server_{current_time}.log"

## 服务启动：
server_start.bat执行

## 所需依赖

requirements.txt文件参照
