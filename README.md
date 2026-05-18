# Video to GIF API

基于 **FastAPI** 的小服务：传入**可直接下载的视频 URL**，用 **FFmpeg** 转成 GIF，并通过 HTTP 返回可访问的 GIF 链接。临时文件会按策略清理。

## 功能

- `POST /video2gif` — 下载视频（如 mp4），转为 GIF，响应里返回 GIF 的 URL  
- `GET /health` — 健康检查  
- `POST /cleanup` — 手动清理 `tmp_video` 下超过 24 小时的文件  
- 后台按间隔执行定时清理（与 `main_api.py` 中配置一致）

## 环境要求

- Python 3.10+（推荐）  
- 系统已安装 **ffmpeg** 且在 `PATH` 中（`ffmpeg -version` 可执行）

## 快速开始

```bash
cd video2gif
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main_api.py
```

默认监听 `http://0.0.0.0:15999`。接口文档：[Swagger UI](http://127.0.0.1:15999/docs)。

### 环境变量（可选）

| 变量 | 说明 | 默认 |
|------|------|------|
| `PORT` | 监听端口 | `15999` |
| `PUBLIC_BASE_URL` | 响应里 GIF 完整 URL 的前缀（不要末尾 `/`） | `http://127.0.0.1:{PORT}` |

反向代理或自定义域名时设置 `PUBLIC_BASE_URL`，例如：

```bash
export PUBLIC_BASE_URL=https://your-domain.com
export PORT=15999
python main_api.py
```

GIF 地址形如：`{PUBLIC_BASE_URL}/tmp_video/<id>.gif`（由 FastAPI `StaticFiles` 挂载 `./tmp_video`）。

## API

### `POST /video2gif`

请求体 JSON：

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `url` | string | 是 | — | 视频直链 |
| `fps` | int | 否 | 5 | 约 1–60 |
| `scale` | float | 否 | 0.5 | 相对宽高缩放（0.5 ≈ 一半宽高） |

示例：

```bash
curl -s -X POST "http://127.0.0.1:15999/video2gif" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/demo.mp4","fps":8,"scale":0.5}'
```

成功时响应示例：

```json
{
  "gif_path": "http://127.0.0.1:15999/tmp_video/a1b2c3d4.gif",
  "message": "GIF conversion succeeded"
}
```

### `GET /health`

```bash
curl -s http://127.0.0.1:15999/health
```

### `POST /cleanup`

```bash
curl -s -X POST http://127.0.0.1:15999/cleanup
```

## 本地 CLI（不启动服务）

```bash
python video_to_gif.py /path/to/input.mp4 -o out.gif --fps 8 --scale 0.5
```

## 测试脚本

```bash
pip install -r requirements-dev.txt
export VIDEO_URL="https://example.com/your-video.mp4"
python test_api.py
```

## 目录结构

```
video2gif/
├── main_api.py           # FastAPI 应用
├── video_to_gif.py       # 本地 ffmpeg 命令行封装
├── test_api.py           # 示例 HTTP 调用（勿提交带签名/私有的 URL）
├── requirements.txt
├── requirements-dev.txt  # test_api 额外依赖
├── README.md
├── .gitignore
├── tmp_video/            # 运行时创建（已 gitignore）
└── logs/                 # 滚动日志（已 gitignore）
```

## 说明

- GIF 往往比原视频大，可适当降低 `fps` 和 `scale`。  
- 视频下载超时默认 300 秒；若需更长可在 `main_api.py` 中调整 `httpx.AsyncClient(timeout=...)`。  
- 若部署在生产环境，建议在网关侧限制并发、请求体大小与来源，并按机器资源调优。
