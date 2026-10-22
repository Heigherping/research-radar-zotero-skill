# 每日检索与分析

## 候选池与时间

根据实际运行日计算滚动区间，写明起止时间。默认从一个月开始，高相关证据不足再扩展到 3、6、12、24、36 个月，最多三年。更早方法可作为明确标注的背景，不冒充近期推荐。

优先可靠学术源：arXiv、OpenAlex、Semantic Scholar、Crossref、出版社/会议官网、PubMed 和机构库。仅声称访问了实际可用的来源。来源失败时降级，搜索结果总数不能当成已阅读候选数。

先建立可比较候选池，结合 Title + Abstract + Metadata，而非找到三篇就停止。根据画像比较研究问题、方法价值、工程/应用条件、排除项和时效；相关性及证据质量优先于新颖标题。简要保留候选取舍与实际检索范围，不为凑数降低标准。

## 身份与版本

规范 DOI（去 DOI URL 前缀、忽略大小写）、arXiv（去版本后缀）及 Unicode 题名。ID 优先；题名相近时核对作者、年份与版本关联，不能仅凭标题去重。已推荐研究只有可验证的重要新增证据才再次推荐，标 `Major Update` 并说明变化。

核验最终论文的标题、作者、发表/上传日期和原始入口。可进一步确认 DOI、期刊/会议、机构和 PDF。缺字段省略或标未取得，不补猜。卷期、首次在线、预印本及仓储上传日期分别说明。

## 推荐类型

- **Highly Relevant**：直接对应当前研究问题和决策。
- **Relevant Expansion**：仍高度相关，但提供不同方法、评估或可迁移应用。
- **Trending**：与个人领域有关的新兴研究。可引用实际观察到的多篇工作或核验的关注信号；不能虚构排名、引用速度或下载量。证据不足时用 `Emerging / Trending Candidate`，不宣称整个领域增长。

## 分析字段

每篇保留可核验题录与来源、Analysis Basis、中文 TL;DR、Research Question、Method、Key Findings、Contributions、Why Recommended、Research Takeaways、Related Keywords、原文和 PDF 链接，以及 Zotero 状态。

只读摘要时标 `Abstract + Metadata`，实验规模、参数、数据划分、指标及数值结论只写摘要明确提供的信息。全文部分可用时说明实际读到了哪些部分，不宣称完整审读。

Why Recommended 必须映射到画像里的具体研究问题、方法或设计取舍。Takeaways 区分原文结论、迁移条件和本项目设想；给一个可执行的小实验或核查动作，避免把相邻领域结果写成本机/本样品已证实的结果。

## 文件与历史

`Daily Papers/YYYY-MM-DD.md` 是唯一新增的论文分析页面，不创建单篇永久笔记。现有用户模板优先。

历史记录至少包含 `title`, `doi`, `arxiv_id`, `semantic_scholar_id`, `openalex_id`, `source`, `published_date`, `recommend_date`, `recommend_type`, `paper_url`；未知值用 null。保留旧记录，版本别名可附于同一条目。不将完整分析放进 JSON。

若全部检索来源失败，写明当天检索失败，不添加虚构历史。推荐完成但 Zotero 不可用时仍保留 Daily，并在页末列出同步待处理项。
