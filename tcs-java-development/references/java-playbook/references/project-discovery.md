# 项目侦察与版本识别

## 目标

用最少的只读检查回答四个问题：项目怎样构建、改动应放哪里、哪些规则必须遵守、怎样验证。

## 侦察顺序

1. 查找仓库根和目标路径上的 `AGENTS.md`、README、CONTRIBUTING、架构说明。
2. 查看 `git status` 与目标文件 diff，保护用户已有改动。
3. 定位构建入口：
   - Maven：`pom.xml`、`.mvn/`、`mvnw`、`mvnw.cmd`
   - Gradle：`settings.gradle*`、`build.gradle*`、`gradle/libs.versions.toml`、`gradlew*`
4. 确认版本来源：
   - Maven properties、parent/BOM、compiler/release、toolchains
   - Gradle Java toolchain、plugins、version catalog、wrapper distribution
   - CI 镜像、容器基础镜像、`.java-version`、SDKMAN/Devbox/Nix 配置
5. 识别模块依赖与启动入口，找到同类型功能、异常处理、DTO、Repository 和测试样例。
6. 从 CI 或 wrapper 推导验证命令；不要优先调用系统全局 Maven/Gradle。

## 需要记录的事实

```text
仓库/模块：
JDK 版本与证据：
构建工具及 wrapper 版本：
框架/BOM 版本：
测试与静态检查：
目标代码与相邻模式：
仓库已有未提交改动：
可用验证命令：
```

## 多模块注意事项

- 区分聚合模块与父 POM；不要假设模块只从根目录构建。
- Gradle 中确认 included builds、project path、插件约定与版本目录。
- 只改目标模块时，仍要检查被依赖模块与下游公开接口。
- 共享 DTO、数据库迁移、消息 schema 与 BOM 变更通常具有跨模块影响。

## 版本决策

- 如果当前版本可以完成任务，默认不升级。
- 必须升级时，列出原因、兼容矩阵、迁移步骤、回滚点和验证范围。
- 不把示例代码的最新语法复制到较低语言级别项目。
- Spring Boot 管理的依赖优先通过其 BOM/依赖管理覆盖；单独改写托管版本前说明原因。

## 常见验证命令选择

以下只是候选，实际以仓库脚本和 CI 为准：

```powershell
# Maven Wrapper (Windows)
.\mvnw.cmd -pl <module> -am test

# Gradle Wrapper (Windows)
.\gradlew.bat :<module>:test
```

不要在未确认模块名、profile、测试分组或外部依赖前机械执行全仓构建。
