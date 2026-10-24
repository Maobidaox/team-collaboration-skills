# NumPy 与 Pandas 数据处理速查

> 用途：AI 项目数据加载、清洗、特征处理的标准写法与性能规范。

## 一、NumPy 核心
- 创建：`np.array`、`np.zeros/np.ones/np.arange/np.linspace`、`np.random.randn`
- 形状：`reshape` / `ravel` / `transpose` / `np.newaxis`（扩维）
- 向量化：**禁止用 Python 循环逐元素计算**，用数组运算（`+ - * /`、`np.where`、`np.dot`、`np.sum(axis=)`）
- 广播：形状不匹配时按规则扩展，`(3,1) + (1,4) → (3,4)`
- 聚合：`sum/mean/std/min/max`、`np.argmax`、`np.unique`、`np.clip`
- 随机：`np.random.seed()` 固定种子；`np.random.choice/permutation`

## 二、Pandas 高频操作
- 读取：`pd.read_csv/read_parquet`（大数据用 parquet，比 csv 快数倍且保留类型）
- 筛选：行 `df.loc[条件]`、`df.iloc[位置]`；列 `df["col"]` / `df[["a","b"]]`
- 缺失值：`isna()` 定位 → `dropna` / `fillna`（均值/中位数/前向填充）
- 分组聚合：`df.groupby("cat")["value"].agg(["mean","count","sum"])`
- 合并：`pd.merge(df1, df2, on="key", how="left")`（明确 how，避免默认行为误判）
- 类型：`astype("category")`（低基数字符列省内存）、`pd.to_datetime`、`pd.to_numeric`
- 去重：`drop_duplicates(subset=[...], keep="first")`

## 三、性能规范（易踩坑）
| 写法 | 性能 | 说明 |
| --- | --- | --- |
| 向量化/内置函数 | 最快 | `df["a"] + df["b"]`、`str.contains` 等 |
| `apply` | 慢 | 仅在无向量化替代时用，勿循环行 |
| `iterrows` 循环 | 最慢 | 禁止，换向量化或 `itertuples` |
| 链式赋值 | 隐患 | `df[df.x>0]["y"]=1` 触发 SettingWithCopyWarning，用 `df.loc[df.x>0, "y"]=1` |

## 四、数据清洗标准流程
1. 概览：`df.info()` / `df.describe()` / `df.isna().sum()` / `df.duplicated().sum()`
2. 处理缺失：区分"真缺失"与"业务默认值"（如 0 表示无）
3. 处理异常值：先 `describe` 看分布，`clip` 或按业务规则剔除，不盲目删
4. 统一格式：时间、金额单位、字符串去空格/大小写
5. 特征编码：类别列 → 标签编码（有序）或独热编码（无序，交 sklearn 处理）
6. 划分：`train_test_split` 要在**任何填充/缩放之前**，防止数据泄露

## 五、训练数据接口规范
- 特征与标签分离：`X = df[features]`，`y = df["target"]`
- 特征列清单与数据类型保持稳定，服务端与训练端用同一 schema（可存 json 校验）
- 训练集/验证集按时间或分层划分（`stratify=y` 保类别均衡）
