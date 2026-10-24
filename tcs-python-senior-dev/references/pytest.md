# pytest 测试实践手册

> 用途：Python 项目的测试编写规范，保证测试可靠、可重复、有覆盖率。

## 一、测试分层
- 单元测试：单函数/单类，不碰网络与数据库
- 集成测试：连真实数据库/接口，用测试库
- 端到端：完整用户路径，数量少、跑得慢，单独 job
- 命名：`test_<被测函数>_<场景>_<期望>`，如 `test_create_order_with_empty_cart_raises`

## 二、fixture 使用
- scope 选择：`function`（默认，互不影响）→ `class` → `module` → `session`（跨用例复用）
- `yield` fixture 做 teardown：前段准备，yield 后段清理
- `autouse=True` 仅用于全局必要准备（如环境变量），少用避免隐式依赖
- 依赖注入：fixture 依赖另一个 fixture 时直接作为参数
- 独立可重复：测试不依赖执行顺序、不依赖共享可变状态

## 三、参数化与断言
- `@pytest.mark.parametrize("输入,期望", [...])` 覆盖边界：空值、None、超长、异常输入
- 断言用原生 `assert` + 清晰消息：`assert result == expected, f"got {result}"`
- 异常断言：`with pytest.raises(ValueError, match="非法参数"):`
- 浮点比较：`pytest.approx`，勿用 `==`

## 四、Mock 与补丁
- `monkeypatch.setattr(module, "func", fake)`（fixture 级，自动还原）
- `unittest.mock.patch` / `patch.object` 用于函数级
- 只 mock 边界：mock 外部 IO（网络、时间、随机），不 mock 被测函数自身逻辑
- 断言调用：`mock.assert_called_once_with(...)`

## 五、异步与 Web 测试
- `pytest-asyncio`：`@pytest.mark.asyncio` 或 asyncio_mode=auto
- FastAPI：`httpx.AsyncClient(transport=ASGITransport(app=app))` 测接口，不启真实端口
- 数据库：事务回滚 fixture（每用例回滚）或用临时库，禁止污染开发数据

## 六、覆盖率与 CI
- `pytest --cov=app --cov-report=term-missing`，关键模块目标 ≥ 80%
- 覆盖重点是分支而非行号：`--cov-branch`
- 未覆盖代码逐条评估：不达标的是"缺测试"还是"死代码"
- CI 门禁：单测全绿 + 覆盖率阈值 + lint 通过才合并
