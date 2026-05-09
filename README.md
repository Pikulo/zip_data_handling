# 📦 压缩文件处理器 (Streamlit版)

一个基于 Streamlit 的网页版压缩文件提取工具，支持 RAR、ZIP、7z 等常见压缩格式。

## ✨ 功能特点

- **多格式支持**：支持 RAR、ZIP、7z、TAR、GZIP、BZIP2、XZ 格式
- **多线程处理**：可配置线程数，并行处理文件提取
- **智能过滤**：自动跳过临时文件和用户文件，可自定义过滤规则
- **一键下载**：处理完成后可直接下载提取结果
- **响应式设计**：支持桌面端和移动端使用
- **Web 界面**：无需安装本地软件，浏览器中直接使用

## 🚀 快速开始

### 环境要求

- Python 3.8+
- macOS/Linux/Windows

### 安装依赖

```bash
# 克隆项目
git clone <your-repo-url>
cd <project-directory>

# 安装依赖
pip install -r requirements_streamlit.txt
```

### 运行应用

```bash
streamlit run streamlit_app.py
```

启动后，在浏览器中打开 `http://localhost:8501` 即可使用。

## 📖 使用方法

1. **上传文件**：点击"选择压缩文件"或直接拖拽文件到上传区域
2. **选择输出**：默认使用临时目录，可自定义输出路径
3. **配置过滤**：在侧边栏设置线程数和文件过滤规则
4. **开始处理**：点击"开始处理"按钮
5. **下载结果**：处理完成后可下载 ZIP 文件到本地

## ⚙️ 配置选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| 线程数 | 同时处理的文件数量 | 4 |
| 跳过 User. 文件 | 是否跳过以 User. 开头的文件 | 是 |
| 自定义过滤规则 | 逗号分隔的跳过前缀 | User.,temp_,. |

## 📦 依赖项

```
streamlit>=1.28.0
rarfile>=4.0
py7zr>=0.20.0
```

## 🛠️ 技术栈

- **前端**：Streamlit
- **后端**：Python
- **压缩库**：rarfile、py7zr、zipfile
- **并发处理**：concurrent.futures.ThreadPoolExecutor

## 📝 文件结构

```
.
├── streamlit_app.py          # 主应用文件
├── requirements_streamlit.txt # 依赖配置
├── README.md                 # 项目说明
└── LICENSE                   # MIT 许可证
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

---

Made with ❤️ by Pikulo