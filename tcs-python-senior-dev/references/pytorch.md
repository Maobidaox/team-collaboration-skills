# PyTorch 深度学习速查

> 用途：PyTorch 模型训练与推理的标准写法、易错点与最佳实践。

## 一、张量基础
- 创建：`torch.tensor` / `torch.zeros` / `torch.randn`；指定 `dtype=torch.float32`（默认）
- 设备：`device = "cuda" if torch.cuda.is_available() else "cpu"`，数据与模型都 `.to(device)`
- 形状：`reshape` / `permute` / `unsqueeze` / `squeeze`；`tensor.shape` 检查
- 与 NumPy 互转：`torch.from_numpy(x)` / `t.numpy()`（注意共享内存）

## 二、自动求导
- `x.requires_grad_(True)` 开启梯度；`loss.backward()` 反向传播
- 推理/评估时用 `with torch.no_grad():` 关梯度，省显存提速
- `optimizer.zero_grad()` 必须在 `backward()` **之前**调用（梯度默认累加）

## 三、数据加载
```python
class MyDataset(Dataset):
    def __getitem__(self, i): ...   # 返回 (x, y)
    def __len__(self): ...
loader = DataLoader(ds, batch_size=32, shuffle=True,
                    num_workers=4, pin_memory=True)
```
- 文本/图像预处理（tokenize、归一化）放 Dataset 内或 transform，保证训练/推理一致
- `pin_memory=True` + GPU 可加速传输；`num_workers` 按机器核数设

## 四、模型定义
```python
class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(128, 10)
    def forward(self, x):
        return self.fc(x)
```
- 只用 `nn.Module` 子类组织层；简单结构可用 `nn.Sequential`
- 参数访问：`model.parameters()` 传给 optimizer

## 五、训练循环标准模板
```python
model.train()                        # 训练模式（启用 Dropout/BatchNorm 统计）
for x, y in loader:
    x, y = x.to(device), y.to(device)
    optimizer.zero_grad()
    out = model(x)
    loss = criterion(out, y)
    loss.backward()
    optimizer.step()
# 评估时
model.eval()                         # 评估模式（关闭 Dropout）
with torch.no_grad():
    ...
```
- 损失：分类 `nn.CrossEntropyLoss`（自带 softmax，模型最后一层**不加** softmax）、回归 `nn.MSELoss`
- 优化器：`optim.Adam(model.parameters(), lr=1e-3)`；学习率调度 `StepLR`/`ReduceLROnPlateau`

## 六、保存与加载
```python
torch.save(model.state_dict(), "model.pt")      # 只存权重（推荐）
model.load_state_dict(torch.load("model.pt", map_location=device))  # 加载到当前设备
```
- 不整模型 `torch.save(model)`（跨环境/版本易坏）
- 保存时附带：`{"state_dict":..., "config":..., "metrics":...}`，便于复现
- 多 GPU 训练（DataParallel/DDP）保存的权重带 `module.` 前缀，加载时需 `strip_prefix` 或 `load_state_dict(..., strict=False)` 处理

## 七、常见坑清单
| 坑 | 表现 | 正确做法 |
| --- | --- | --- |
| device 不一致 | RuntimeError: Expected all tensors on same device | 数据、模型统一 `.to(device)` |
| 忘记 zero_grad | loss 异常波动 | backward 前调用 |
| 评估忘切 eval | 结果偏随机 | `model.eval()` + `no_grad` |
| 训练/推理预处理不一致 | 线上效果暴跌 | 预处理逻辑唯一化（同 Dataset/transform） |
| 随机种子未固定 | 结果不可复现 | `torch.manual_seed` + `numpy.random.seed` + `random.seed` |
| 显存不足 | CUDA OOM | 减 batch、`no_grad`、`torch.cuda.empty_cache()`、梯度累积 |
| 数据泄露 | 评估虚高 | 切分/预处理只基于训练集 |

## 八、常用模型速览（HuggingFace 生态）
- 文本分类/生成：`AutoModelForSequenceClassification` / `AutoModelForCausalLM`
- 嵌入：`AutoModel` + mean pooling 或 `sentence-transformers`
- 图像：`torchvision.models`（resnet/vit）；`transformers` 的 ViT/CLIP
- 微调入门：`Trainer`（HF）封装训练循环，配 `TrainingArguments`
