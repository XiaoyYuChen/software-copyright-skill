# software-copyright-skill

面向 [Cursor Agent Skills](https://cursor.com/docs/skills) 的软件著作权（软著）申请助手：从项目自动采集信息，整理基本信息，生成程序鉴别材料 PDF，并支持材料合规审核。

## 功能

- **制作材料**：基本信息草稿、程序鉴别材料（60 页 md/html/pdf）、文档鉴别材料指引
- **审核材料**：按登记要求逐项检查，输出补正建议

在 Cursor 中提及「申请软著」「软件著作权」「审核软著材料」等关键词时，Agent 会自动加载本 Skill。

## 目录结构

符合 Cursor 标准 Skill 布局（[官方文档](https://cursor.com/docs/skills)）：

```text
software-copyright-skill/
├── SKILL.md              # 主指令（必填）
├── README.md             # 本文件：安装与使用说明
├── LICENSE               # Apache-2.0
├── scripts/              # 可执行脚本
│   ├── generate_program_pdf.py
│   └── 程序鉴别材料-转PDF.bat
├── references/           # 按需加载的详细规则
│   ├── reference.md
│   ├── doc-template.md
│   └── review-checklist.md   # 审核/审查完整清单
└── assets/               # 静态模板与样例
    ├── code-pages-60.html
    ├── 说明文档模板.doc   # 文档鉴别材料 Word 模板
    └── 说明文档模板.md    # 文档鉴别材料 Markdown 骨架
```

## 安装

将本仓库克隆或复制到 Cursor Skills 目录之一：

| 作用域 | 路径（Windows 示例） |
|--------|----------------------|
| 全局（推荐） | `%USERPROFILE%\.cursor\skills\software-copyright-skill\` |
| 项目内 | `<项目根>\.cursor\skills\software-copyright-skill\` |

安装后重启 Cursor，或在对话中使用 `/software-copyright-skill` 手动触发。

## 依赖

生成程序鉴别材料 PDF 需要 Python 3 与 ReportLab：

```bash
pip install reportlab
```

Windows 下 PDF 中文页眉优先使用 `C:\Windows\Fonts\simhei.ttf`；缺失时脚本会回退 CID 字体。

## 快速使用

### 在 Cursor 中（推荐）

对 Agent 说明目标项目路径与软件全称，例如：

> 帮我为 `D:\my-app` 申请软著，软件全称「某某管理系统」。

Agent 会按 `SKILL.md` 流程采集信息、生成 `software-copyright/` 目录下的材料，并调用内置脚本生成程序鉴别材料。

### 命令行生成程序鉴别材料

固定输出 **60 页**（前 30 + 后 30，每页 50 行），写入 `<项目根>/software-copyright/`：

```bash
python "%USERPROFILE%\.cursor\skills\software-copyright-skill\scripts\generate_program_pdf.py" ^
  --project-root "D:\my-app" ^
  --project-name "某某管理系统"
```

Windows 也可双击或命令行运行：

```bat
"%USERPROFILE%\.cursor\skills\software-copyright-skill\scripts\程序鉴别材料-转PDF.bat" "D:\my-app" "某某管理系统"
```

输出文件：

- `software-copyright/基本信息.md`（由 Agent 整理）
- `software-copyright/程序鉴别材料.md`
- `software-copyright/code-pages-60.html`
- `software-copyright/程序鉴别材料.pdf`

## 输出目录

默认在目标项目根目录创建 `software-copyright/`。若项目已有 `Doc/`、`Docs/`、`项目文档/`，Skill 会优先在该处组织文档（详见 `SKILL.md`）。

## 许可证

[Apache License 2.0](LICENSE)

## 相关链接

- 仓库：<https://github.com/XiaoyYuChen/XiaoyYuChen-software-copyright-skill>
- Cursor Skills 文档：<https://cursor.com/docs/skills>
