# Python 语言规范与常见坑

> 用途：Python 全栈开发专家的基础语言资产。写代码与评审时遵守本规范，识别常见反模式。

## 一、PEP 8 核心规范
- 缩进：4 空格，禁止混用 Tab
- 行宽：≤ 88 字符（Black 默认），长表达式用括号换行
- 命名：函数/变量 `snake_case`，类 `CamelCase`，常量 `UPPER_SNAKE_CASE`，私有成员 `_` 前缀
- import 顺序：标准库 → 第三方 → 本地模块，每组内按字母序
- 空行：顶层函数/类之间 2 空行，类内方法之间 1 空行
- 注释：写"为什么"不写"是什么"，中文注释统一中文标点

## 二、类型标注（Python 3.10+）
- 函数签名必须标注参数与返回值类型
- 常用泛型：`Optional[T]` → `T | None`、`list[T]`、`dict[K, V]`、`Union` → `|`
- 复杂场景：`Literal`（限定取值）、`TypedDict`（字典结构）、`TypeVar`（泛型）、`Protocol`（结构化类型）
- 用 `mypy --strict` 或 pyright 做静态检查，纳入 CI

## 三、常见坑（评审必查）
| 坑 | 说明 | 正确做法 |
| --- | --- | --- |
| 可变默认参数 | `def f(x=[])` 共享同一对象 | 默认值用 `None`，函数内初始化 |
| 闭包延迟绑定 | 循环内 `lambda i: i` 全部取末值 | 用默认参数绑定 `lambda i=i: i` 或 functools.partial |
| `is` vs `==` | `is` 比较身份，小整数/短字符串有缓存 | 与 `None` 比较用 `is`，其余用 `==` |
| 浅拷贝 | `list.copy()`/`[:]` 只拷贝外层 | 嵌套结构用 `copy.deepcopy` |
| 循环内改列表 | 遍历时删除元素会跳项 | 用列表推导/新建列表/filter |
| 字符串拼接 | `+` 在循环中是 O(n²) | 用 `"".join(...)` 或 f-string |
| 字典遍历时修改 | RuntimeError | 先收集 key 再删除，或重建字典 |
| `except Exception` | 裸 `except:` 会吞掉 KeyboardInterrupt | 明确捕获异常类型，必要时 `raise` |
| 线程与 GIL | CPU 密集多线程无加速 | IO 密集用线程，CPU 密集用 ProcessPoolExecutor |
| 可变对象做 key | list/dict 不可哈希 | 转 tuple/frozenset |

## 四、依赖与环境管理
- 项目用 `pyproject.toml` 声明依赖，`uv` / `pip-tools` 管理并锁定版本
- 环境隔离：`venv` / `uv venv`，禁止全局安装
- 生产依赖与开发依赖分离（`[project.optional-dependencies]`）
- 升级依赖前检查 breaking change，锁文件入版本库

## 五、代码质量工具链
- 格式化：Black（或 Ruff format）
- Lint：Ruff（替代 flake8/isort/pyupgrade）
- 类型：mypy / pyright
- 安全扫描：pip-audit / bandit
- 以上全部接入 pre-commit 与 CI
