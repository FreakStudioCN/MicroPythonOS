# MicroPythonOS 代码架构梳理

本文档用于快速理解仓库中的核心模块、职责边界以及推荐的改动入口，帮助后续维护时降低耦合。

## 1. 总体分层

MicroPythonOS 仓库可按职责拆分为四层：

1. **固件与底层 C 能力层**：`c_mpos/`、`secp256k1-embedded-ecdh/`、`micropython-camera-API/`
2. **MicroPython 运行时与扩展层**：`lvgl_micropython/`、`micropython-nostr/`
3. **系统资源与应用层**：`internal_filesystem/`、`freezeFS/`、`manifests/`
4. **工程支撑层**：`scripts/`、`tests/`、`patches/`、`.github/workflows/`

## 2. 目录职责映射

| 目录 | 职责 | 建议改动范围 |
|---|---|---|
| `c_mpos/` | 主固件构建与硬件相关 C 代码 | 硬件驱动、主板能力、性能/内存优化 |
| `lvgl_micropython/` | LVGL 与 MicroPython 适配代码 | GUI 组件、UI 性能、渲染行为 |
| `internal_filesystem/` | 设备内置应用与库（`apps/`、`lib/`、`builtin/`、`data/`） | Python 业务逻辑、内置资源 |
| `freezeFS/` | 冻结到固件的文件系统资源 | 启动必需脚本、关键静态资源 |
| `manifests/` | 冻结/打包清单 | 固件内容装配与裁剪 |
| `scripts/` | 构建与开发辅助脚本 | CI/CD、本地开发工具 |
| `tests/` | 自动化测试与截图基线 | 回归测试、截图对比 |
| `patches/` | 第三方补丁集合 | 版本升级时的 patch 管理 |

## 3. 依赖方向（建议保持）

为减少循环依赖，建议遵守如下单向依赖：

- `internal_filesystem/apps` → `internal_filesystem/lib`
- `internal_filesystem/*` → 通过 API 调用底层能力，避免直接绑定具体驱动实现
- 构建与发布逻辑集中在 `scripts/`、`manifests/`，避免分散在业务目录
- 第三方修改优先放在 `patches/`，避免直接改 vendor 源码导致升级困难

## 4. 推荐开发入口

### 4.1 功能开发

- 新增设备端 Python 功能：优先放 `internal_filesystem/apps/`，公共逻辑下沉到 `internal_filesystem/lib/`
- 新增底层能力（C/驱动）：放 `c_mpos/src/` 或对应外设目录，并提供清晰的 MicroPython 绑定入口

### 4.2 构建裁剪

- 固件内容增减：优先调整 `manifests/` 与 `freezeFS/`
- 不同板型差异：集中在 `c_mpos/` 的构建配置，不在应用层做条件分支堆叠

### 4.3 测试与回归

- Python 逻辑回归：放 `tests/base/`
- 视觉相关改动：更新 `tests/screenshots/` 基线并记录差异

## 5. 架构整理后的维护约定

1. **同层聚合**：相同职责代码放同一目录，避免“工具函数散落多处”。
2. **边界清晰**：应用层不直接依赖硬件实现细节，统一走封装接口。
3. **清单驱动**：固件内容通过 manifest/freeze 统一声明，避免隐式打包。
4. **补丁可追溯**：第三方改动必须以 patch 形式管理，并说明来源与版本。

## 6. 后续可执行的整理清单

- 为 `internal_filesystem/lib/` 增加按领域分组（例如 `crypto/`、`net/`、`ui/`）
- 为 `scripts/` 增加 `README`，标明每个脚本输入输出
- 为 `patches/` 增加命名规范（`<upstream>-<version>-<topic>.patch`）
- 在 CI 增加目录边界检查（例如禁止 `apps/` 直接 import 私有驱动模块）
