# uPyStore

MicroPythonOS 应用商城客户端，包名 `com.freakstudio.upystore`，版本 `1.0.0`。代码使用系统的 Activity、InputActivity、TaskManager、DownloadManager 和 AppManager；不修改板级配置或系统全局代码。

## 已验证环境

D-Shell / ESP32-S3 N16R8，16 MB Flash、8 MB PSRAM，240 × 320 ST7789V + GT911，显示 SPI 80 MHz。测试固件为 MicroPythonOS 0.21.2，代码基线 `8484908a5ceade80a7a5854925b85d662a3b480b`；运行分区镜像 SHA256 为 `c72e27e795441c4ab2077e97cced514ea7ac825be0e29851a5ca790ea49fd0a9`。本 App 的部署不需要重新烧录固件。

## 功能与接口

- 首页使用 `GET https://upystore.io/api/v1/apps?limit=6&page=1&q=`，支持分页和搜索。
- Catalog 检查 `GET https://upystore.io/app_index.json` 的兼容目录。
- 详情使用 `GET /api/v1/apps/{slug}`，从当前实际返回的 `versions` 中选择与应用当前 revision 对应的包。
- 下载使用版本记录的 HTTPS `download_url`，检查发布大小和 SHA256，再解包到暂存目录、检查 manifest 和入口，最后替换 `/apps/{fullname}`。
- Open installed app 使用 AppManager 启动安装后的应用。所有主要按钮加入 LVGL 焦点组。
- 断网、404/410、403、超时和校验错误显示提示；联网后点 Retry 重新请求。失败下载清理临时文件，替换前校验失败保留已有应用。

不会自动发送设备画像或安装统计，不使用账户密码，不调用系统固件更新接口。安装代码拥有普通 MicroPythonOS App 的执行权限；仅安装可信来源的应用。

## 安装

1. 在 MicroPythonOS 的 WiFi 设置中连接可用的 2.4 GHz 网络。
2. 使用交付的 `com.freakstudio.upystore_r1.mpk`。核对交付报告中该文件的 SHA256。
3. 通过系统支持的文件传输方式把 MPK 放到设备 `/upystore-install.mpk`，然后在已正常启动的系统 REPL 执行：

```python
from mpos import AppManager
AppManager.install_mpk('/upystore-install.mpk', '/apps/com.freakstudio.upystore')
AppManager.refresh_apps()
AppManager.start_app('com.freakstudio.upystore')
```

MPK 安装成功后源包会被系统删除。也可以在文件管理器中打开 MPK，使用系统安装界面。

如使用 mpremote 传文件，先结束其他串口工具的连接。文件传输可能中断当前 OS 的 asyncio 循环，传输完成后复位设备、等待正常桌面启动，再打开 REPL 执行安装；不要在已被 Ctrl+C 中断的 OS 循环上继续评估 App 是否正常。串口号以实际枚举为准，本次为 `COM11`。

## 从代码打包与检查

在仓库根目录使用 CPython：

```powershell
python -B -m unittest discover -s internal_filesystem/apps/com.freakstudio.upystore/tests -p 'test_*.py'
python -m zipfile -c com.freakstudio.upystore_r1.mpk internal_filesystem/apps/com.freakstudio.upystore
python -m zipfile -t com.freakstudio.upystore_r1.mpk
Get-FileHash com.freakstudio.upystore_r1.mpk -Algorithm SHA256
```

MPK 的首项必须是 `com.freakstudio.upystore/` 目录；manifest 位于该目录根部。不要包含 `__pycache__` 或 `.pyc`。`tests/` 为主机 CPython 回归测试，不由设备 App 导入。仓库标准检查为 `make lint` 和 `make syntax-tests`。

## 实机复现与录制

1. 打开桌面的 uPyStore，等目录加载；点 Next/Prev 验证分页。
2. 点 Catalog，观察兼容目录应用数；点 Search，输入 `CC Skill Smoke` 并保存。
3. 点搜索结果，核对 `com.example.cc_skill_smoke`、`1.0.0`、revision `1`。
4. 在详情区域上下滑动，点 Install / update。观察 Downloading、Verifying、Installing 和 Installed 状态。
5. 点 Open installed app，操作计算器 `2 + 3 =`，应显示 `5`；返回商城应能继续操作。
6. 在系统设置关闭 WiFi，再返回商城点 Retry，确认离线提示；重新连接后点 Retry，确认恢复。
7. 记录固件版本、被测应用与包 revision、时间及结果。实拍视频应包含设备外观和上述操作，设备截图不能替代实拍。

2026-11-19 的已选测试包：3872 字节，SHA256 `44b63bb4af00613edea5ce01069aa58e3032a7dad81a7e350b263c35a75418b6`。服务端内容会变化，后续以实际响应为准。旧示例 `io-kontinyu-upystore-sample` 当日仍返回 404，不能因为网站恢复而认定该包可用。

## 范围与限制

单个 MPK 最大 2 MiB、最多 256 个 ZIP 项，展开后最大 4 MiB，并预留 64 KiB 可用 Flash。仅接受同源 HTTPS 下载地址及本固件支持的 ZIP 格式；缺少文件大小、SHA256、入口或 OS/API 不兼容时拒绝安装。目录响应受内存上限约束，兼容目录上限 700000 字节。

安装暂存目录为 `/data/upystore/stage/`，备份为 `/data/upystore/backup/`。正常异常路径会清理暂存并恢复重命名失败前的旧目录。断电期间的跨目录替换不是事务；检测到旧备份时会停止后续安装，应先人工核对备份、目标 manifest 与入口，保留需要的数据，再恢复。未验证全部商城应用、付费/登录、遥测、OTA 或长时间压力测试。
