# Python AI 技术栈导览与选型

> 用途：AI 相关问题的第一站。先明确"这个需求属于 AI 的哪一层、用什么库"，再给方案，避免选型混乱。

## 一、AI 技术栈分层

| 层级 | 典型库 | 解决什么 |
| --- | --- | --- |
| 数据处理 | NumPy / Pandas / Polars | 数值计算、表格数据清洗与特征工程 |
| 传统机器学习 | scikit-learn / XGBoost / LightGBM | 结构化数据的分类、回归、聚类、特征重要性 |
| 深度学习 | PyTorch（首选）/ TensorFlow | 图像、文本、序列等非结构化数据的模型训练 |
| LLM 应用 | Hugging Face Transformers / LangChain / LlamaIndex | 大模型调用、RAG、Agent、提示词编排 |
| 向量检索 | FAISS / Chroma / pgvector / Milvus | 语义检索、相似度召回（RAG 核心） |
| 部署推理 | ONNX Runtime / vLLM / FastAPI | 模型服务化、量化加速、在线推理 |

## 二、选型建议（按场景）

| 场景 | 推荐 | 说明 |
| --- | --- | --- |
| 表格数据、中小规模 | scikit-learn + XGBoost | 快、稳、可解释性好，先于深度学习尝试 |
| 图像/文本/序列 | PyTorch | 生态最活跃，HuggingFace 默认基于它 |
| 调用大模型 API | OpenAI SDK / 国内大模型 SDK | 不自己训模型，只做应用编排 |
| 私有部署大模型 | vLLM + Transformers | 高吞吐推理，兼容 OpenAI 协议 |
| 语义检索/RAG | 中小规模 FAISS/Chroma，生产 pgvector/Milvus | 按数据量与并发选 |
| 数据分析为主 | Pandas + Polars（大数据量） | Polars 比 Pandas 快数倍，内存友好 |

## 三、版本与环境兼容（易错点）
- Python 版本：PyTorch 2.x 需 Python 3.9+；新库（如新版 transformers）常要求 3.10+
- GPU：CUDA 版本必须与 PyTorch 预编译轮子匹配（`pip install torch --index-url https://download.pytorch.org/whl/cu121`）
- 环境管理：AI 项目依赖极易冲突，用 `uv`/conda 隔离环境；`uv.lock`/`requirements-lock` 锁定版本
- 检查工具：`nvidia-smi` 看驱动与显存；`torch.cuda.is_available()` 验证 PyTorch 能用 GPU

## 四、项目结构建议（AI 服务）
```
project/
  data/            # 原始与处理后数据（不入库）
  src/
    data/          # 数据加载与预处理
    features/      # 特征工程
    models/        # 模型定义与训练脚本
    serving/       # FastAPI 推理服务
  configs/         # 实验配置（yaml）
  tests/           # 测试（含模型输出形状断言）
  experiments/     # 实验记录（MLflow/tensorboard）
```

## 五、可复现性基线（AI 项目必备）
- 固定随机种子：`random` / `numpy` / `torch.manual_seed` 全部设置
- 实验跟踪：MLflow（指标+模型+参数）或至少每次实验记录 config 与指标
- 数据版本：原始数据不可变，处理脚本可复现；大数据用 DVC
- 模型版本：训练产物与代码版本一一对应，便于回滚
