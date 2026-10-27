import os
# Force disable proxy for local connections to avoid connection issues
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

import os
import queue
import sys
import numpy as np
import sounddevice as sd
import sherpa_onnx

# ----------------- 1. 配置模型路径 -----------------
# 请将这里的路径替换为你下载的 Zipformer 模型文件夹路径
MODEL_DIR = "./sherpa"

encoder = os.path.join(MODEL_DIR, "encoder-epoch-99-avg-1.int8.onnx")
decoder = os.path.join(MODEL_DIR, "decoder-epoch-99-avg-1.int8.onnx")
joiner = os.path.join(MODEL_DIR, "joiner-epoch-99-avg-1.int8.onnx")
tokens = os.path.join(MODEL_DIR, "tokens.txt")
# 检查文件是否存在
for f in [encoder, decoder, joiner, tokens]:
    if not os.path.exists(f):
        print(f"错误: 找不到模型文件: {f}")
        sys.exit(1)

# ----------------- 2. 初始化 Sherpa-onnx 识别器 -----------------
print("正在加载 Zipformer 流式模型...")

# 采用官方标准的高级包装接口直接创建实例
recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
    tokens=tokens,
    encoder=encoder,
    decoder=decoder,
    joiner=joiner,
    num_threads=4,                   # CPU 线程数
    sample_rate=8000,               # 默认采样率
    feature_dim=80,                  # Fbank 特征维度
    decoding_method="greedy_search", # 贪婪搜索解码，延迟最低
    enable_endpoint_detection=True,  # 开启端点检测（自动断句）
    rule1_min_trailing_silence=2.4,  # 说话结束后的静音断句时间（秒）
    rule2_min_trailing_silence=1.2,
    provider="cpu",                  # Windows 默认 CPU 推理
)

# ----------------- 3. 音频流处理队列与配置 -----------------
sample_rate = 8000
# 每次读取 100ms 长度的音频切片传入流中
samples_per_read = int(0.1 * sample_rate) 
audio_queue = queue.Queue()

def record_callback(indata, frames, time, status):
    """麦克风输入回调函数，将音频数据塞入队列"""
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(indata.copy())

# ----------------- 4. 启动实时录音与识别 -----------------
print("\n>>> 模型加载成功！请开始说话... (按 Ctrl+C 退出)")

# 创建一个识别输入流
stream = recognizer.create_stream()
last_text = ""

try:
    # 启动麦克风监听
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32", callback=record_callback):
        while True:
            # 持续从队列获取 100ms 的音频并喂给模型
            samples = audio_queue.get()
            stream.accept_waveform(sample_rate, samples.flatten())
            
            # 驱动模型进行流式解码
            while recognizer.is_ready(stream):
                recognizer.decode_stream(stream)
            
            # 检查是否满足断句条件
            is_endpoint = recognizer.is_endpoint(stream)
            
            # 核心修正：最新版 API 直接返回字符串类型，不再有点 text 属性
            current_text = recognizer.get_result(stream)
            
            # 仅在文本更新且不为空时输出，模拟打字机效果
            if current_text and current_text != last_text:
                sys.stdout.write(f"\r实时转写: {current_text}")
                sys.stdout.flush()
                last_text = current_text

            # 如果检测到一句话结束，重置流开启新的一句
            if is_endpoint:
                recognizer.reset(stream)
                print("\n[句子结束]")
                last_text = ""

except KeyboardInterrupt:
    print("\n程序已安全退出。")

