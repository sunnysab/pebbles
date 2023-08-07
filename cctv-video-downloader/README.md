# CCTV-video-downloader

CCTV 视频下载脚本（自用，易用性差） 

## 依赖

在下载流程中，获取下载地址这一步是同步请求的。 `downloader.py` 构造了一个通用的、异步下载文件的类，可以提升下载速度。

- asyncio
- aiohttp
- aiofiles
- requests

本程序调用了 ffmpeg 命令。

## 使用

```python
python3 cctv.py [视频 URL]
```
