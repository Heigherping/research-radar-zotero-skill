# Research Radar + Zotero

一个面向 Codex 等文件式 skill 宿主的科研论文雷达：读取最新研究画像，生成 Obsidian 每日推荐，按授权同步到指定 Zotero 分类，保存合法可得的正文 PDF，并在笔记末尾提醒缺失项。

## 工作流

研究画像 → 多源检索 → 候选比较与版本去重 → 每日分析 → Zotero 指定分类 → 正文附件核验 → 缺失提醒。

- 默认 2 篇高相关 + 1 篇个性化热点，宁缺毋滥。
- 最近一个月优先，必要时分层扩大，最多三年。
- 已有条目及附件复用；分类固定，不跟随界面当前选中项。
- 正式版/接受稿/预印本区分，摘要与全文分析区分。
- 保留用户模板、历史、阅读状态和手动判断，不自动创建永久论文笔记。

## 安装

下载本仓库，将包含 `SKILL.md` 的目录放到 `~/.codex/skills/research-radar-zotero/`，然后在新会话中使用；其他兼容宿主使用其对应 skills 目录。

需要一个可联网检索和操作本地文件的 agent。Zotero 同步需要运行中的 Zotero Desktop 及可用的写入接口；只读数据库助手使用 Python 3.10+ 标准库，无第三方依赖。PDF 内容核验使用宿主可用的 PDF 解析工具。

本仓库是 **agent 工作流 skill**，不是独立运行的论文爬虫或后台服务。附带脚本只做只读核验；论文检索、写入和下载由 agent 的可用工具执行。仅安装 skill 不会自动修改 Zotero，也不会自动创建定时任务。

## 使用

在项目中准备 `Research Profile.md`，优先使用已有 Daily 模板。可参考 `assets/research-radar.example.json` 创建项目自己的 `research-radar.local.json`；确认自动入库授权、目标分类和 SI 偏好后保存配置。

```text
使用 $research-radar-zotero，根据当前项目最新的 Research Profile.md 生成今日推荐。
允许自动创建 Zotero 条目，全部加入我的“光谱分析”分类，只下载正文 PDF，不含 SI。
把缺失 PDF、分类归入失败或其他同步问题列在 Obsidian 每日页面末尾。
```

```text
使用 $research-radar-zotero，仅补做今天页面里尚未完成的 Zotero/PDF 同步，保留我的阅读判断。
```

需要定时执行时，明确要求宿主创建 Scheduled Task，并指定时间、时区及项目。机器与所需本地应用须保持可用。

## 只读检查

```text
python scripts/zotero_inspect.py status
python scripts/zotero_inspect.py inspect --data-dir <Zotero数据目录> --collection-name 光谱分析 --doi <论文DOI>
```

脚本读取临时一致快照，不写 Zotero SQLite。题名匹配仅产生候选，需要再核对作者与年份；文件存在和 PDF 文件头正确，也不等于内容已核验。

## 验证与隐私

```text
python -m unittest discover -s tests -v
python -m compileall -q scripts
```

仓库不包含个人研究画像、文库 ID、历史推荐、登录凭据或论文文件；实际配置和运行产物应留在用户项目。下载仅使用合法可访问来源，未找到就报告，不承诺每篇都有 PDF。

MIT License。Zotero、Obsidian 与 Codex 为其各自权利人的产品，本项目不是官方插件。
