# scikit-learn 机器学习实践

> 用途：结构化数据的建模标准流程：预处理 → 管道 → 训练评估 → 部署，附防数据泄露规范。

## 一、标准流程
```
数据清洗 → 划分训练/测试 → 预处理（fit 只在训练集） → Pipeline 建模 → 交叉验证 → 评估 → 保存
```

## 二、数据划分
- `train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)`
- 分类任务必须 `stratify`（保类别比例）；时序任务按时间切，禁止随机打乱
- **划分必须先于任何预处理**：填充均值、缩放等一律在训练集上 `fit`，测试集只 `transform`——否则数据泄露

## 三、预处理（Pipeline 内）
- 数值列：`StandardScaler`（标准化，SVM/线性模型必需）/ `MinMaxScaler`（0-1）
- 类别列：`OneHotEncoder(handle_unknown="ignore")`（未知类别容错）
- 缺失值：`SimpleImputer(strategy="median"/"most_frequent")`
- 组合：`ColumnTransformer` 按列类型分派不同预处理，再接入模型

## 四、Pipeline（核心规范）
```python
from sklearn.pipeline import Pipeline
pipe = Pipeline([
    ("prep", ColumnTransformer(...)),
    ("model", RandomForestClassifier(n_estimators=200, random_state=42)),
])
pipe.fit(X_train, y_train)          # 一次完成预处理+训练
y_pred = pipe.predict(X_test)       # 预测时自动应用同一预处理
```
- 优势：预处理与模型绑定，杜绝"训练/推理预处理不一致"
- 网格搜索：`GridSearchCV(pipe, param_grid={"model__max_depth":[...]}, cv=5)`，注意 `model__` 前缀

## 五、模型选择速览
| 场景 | 推荐 | 说明 |
| --- | --- | --- |
| 分类基线 | LogisticRegression | 快、可解释 |
| 表格数据强基线 | RandomForest / XGBoost / LightGBM | 非线性、特征重要性、少调参 |
| 高维稀疏 | LinearSVC / SGDClassifier | 文本等场景 |
| 小样本 | 带正则的线性模型 | 防过拟合 |
| 回归 | Ridge / RandomForestRegressor | 线性与非线性各一 |

## 六、评估
- 分类：`accuracy`（均衡时）、`precision/recall/F1`（不均衡时）、`roc_auc_score`、混淆矩阵
- 回归：`mean_squared_error` / `mean_absolute_error` / `r2_score`
- 交叉验证：`cross_val_score(pipe, X, y, cv=5, scoring="f1_macro")` 比单次划分更可信
- 不均衡处理：`class_weight="balanced"` 或 `SMOTE`，先评估再上采样

## 七、过拟合信号与对策
- 信号：训练分数远高于验证分数；交叉验证方差大
- 对策（按优先级）：简化模型 → 正则（C/alpha）→ 交叉验证调参 → 特征选择 → 加数据
- 特征重要性：`pipe.named_steps["model"].feature_importances_` 定位无用特征

## 八、模型保存与加载
```python
import joblib
joblib.dump(pipe, "model.joblib")          # 保存整个 Pipeline（含预处理）
pipe = joblib.load("model.joblib")         # 加载即可 predict
```
- **安全红线**：joblib/pickle 反序列化可执行任意代码，只加载可信来源的模型文件
- 生产建议：记录模型版本、训练数据版本、指标与特征清单，便于追溯
