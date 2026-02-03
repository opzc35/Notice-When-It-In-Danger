# Notice When It In Danger

实时检测摄像头，当检测到两个及以上的人脸时，自动触发指定按键（可配置）。

## 功能

- 每 0.5 秒检测一次摄像头画面
- 检测到两人或以上时触发按键（支持常见按键名或单个字符）
- 轻量 UI，适合后台运行

## 使用方式

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 启动程序：

```bash
python main.py
```

3. 在 UI 中设置：
   - **触发按键**：如 `space`、`enter`、`esc`、`f1`，或单个字符
   - **摄像头索引**：默认 `0`

## 构建 Windows 程序

本项目已配置 GitHub Actions 自动构建 Windows 可执行程序，输出在 Actions 的 Artifacts 中。

本地构建示例：

```bash
pip install -r requirements.txt pyinstaller
pyinstaller -F -w main.py -n NoticeWhenInDanger
```

## 说明

- 若未识别到摄像头，请检查权限或更换摄像头索引。
- 按键触发带 3 秒冷却时间，避免重复触发。
