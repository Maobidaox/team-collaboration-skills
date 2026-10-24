# AI 模型部署与推理优化

> 用途：把训练好的模型（传统 ML / PyTorch / LLM）服务化的标准做法与加速手段。

## 一、服务化架构
- 形态：FastAPI 封装模型 → `/predict` 接口 → Docker 部署
- 关键原则：**模型加载一次、请求只做推理**（模块级加载，勿在请求内 load）
- 接口规范：请求/响应用 Pydantic 校验，输出形状与类型固定；批量预测用 list 输入
- 健康检查：`/healthz`（存活）+ `/readyz`（模型已加载）
- 并发：推理是 CPU/GPU 密集，用进程/线程池控制并发度，防打爆资源

## 二、模型服务示例结构
```python
model = joblib.load("model.joblib")   # 或 torch.load 后的模型，模块加载一次
@app.post("/predict")
def predict(req: PredictRequest):
    return {"result": model.predict(req.features).tolist()}
```

## 三、推理加速手段（按性价比排序）
| 手段 | 适用 | 收益 |
| --- | --- | --- |
| 批处理（batching） | 高并发在线服务 | 吞吐成倍提升，成本最低 |
| 半精度 FP16 | GPU 推理 | 显存减半、速度提升 |
| 量化 INT8 | 通用 | 体积/延迟下降，精度轻微损失 |
| ONNX 导出 | PyTorch/sklearn 模型 | 跨框架、Runtime 加速 |
| vLLM / TGI | LLM 推理 | 吞吐数倍于原生 Transformers |
| 模型蒸馏/剪枝 | 有训练资源 | 小模型接近大模型效果 |

## 四、PyTorch 部署要点
- 导出：`torch.onnx.export(model, dummy_input, "model.onnx")`，固定输入形状
- ONNX Runtime：`ort.InferenceSession` + `session.run(None, {input_name: x})`
- 显存管理：推理用 `no_grad`；监控 `nvidia-smi`；批次过大 OOM 时降 batch
- CPU 部署：`torch.set_num_threads()` 按核数设，过大反而慢（线程竞争）

## 五、LLM 服务部署（vLLM）
- 启动：`vllm serve <model>`，自带 OpenAI 兼容 API，`/v1/chat/completions` 直接对接现有客户端
- 参数：`--tensor-parallel-size`（多卡）、`--max-model-len`（上下文长度）、`--gpu-memory-utilization`（显存占用比例）
- 吞吐优化：`continuous batching`（vLLM 默认）、`--quantization awq/gptq`（量化模型）
- 指标关注：首 token 延迟、生成吞吐（token/s）、并发下 P50/P99 延迟

## 六、容器与 GPU 部署
- Docker：`nvidia-container-toolkit` 支持 GPU 透传，`docker run --gpus all`
- 镜像：基础镜像 `nvidia/cuda:12.x-runtime`（运行态小），安装推理依赖即可
- 生产：K8s + GPU 节点池，模型放 PVC/对象存储按版本挂载，滚动更新
- 无 GPU 兜底：CPU + 量化小模型，或云推理 API 作为降级通道

## 七、性能评估口径
- 吞吐：QPS（每秒请求数）与 token/s（生成型）
- 延迟：P50 / P99、首 token 延迟（流式场景关键）
- 压测：`locust`/`wrk` 压接口，明确并发数、batch 大小、硬件条件
- 优化原则：先压测拿基线 → 单变量改动 → 对比 → 上线灰度观察
