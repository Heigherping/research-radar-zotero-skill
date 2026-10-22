---
type: moc
---

# 📚 论文阅读状态看板

> 自动汇总 `Research Radar/Daily Papers` 中每个 `### Paper N` 下的论文。
> 在原日报对应论文下修改 `- **阅读状态:** unread`：`unread` = 未读，`reading` = 阅读中，`done` = 已完成。
> 「阅读状态」与「Further Reading Decision」分别记录阅读进度和后续处理决定。

```dataviewjs
const CONFIG = {
  folder: "Research Radar/Daily Papers",
  states: [
    { label: "未读", emoji: "📥", value: "unread" },
    { label: "阅读中", emoji: "📖", value: "reading" },
    { label: "已完成", emoji: "✅", value: "done" },
  ],
};

const aliases = {
  unread: "unread", unreading: "unread", "未读": "unread",
  reading: "reading", "阅读中": "reading",
  done: "done", "已完成": "done",
};
const papers = [];
const pages = dv.pages('"' + CONFIG.folder + '"').sort(p => p.file.name, "desc");
for (const page of pages) {
  const raw = await dv.io.load(page.file.path);
  if (!raw) continue;
  const lines = raw.split(/\r?\n/);
  const blocks = [];
  let current = null;
  // 忽略代码示例中的标题，按日报里的真实 Paper 章节拆分。
  let fence = null;
  for (const line of lines) {
    const marker = line.match(/^\s{0,3}(`{3,}|~{3,})(.*)$/);
    if (fence) {
      if (marker && marker[1][0] === fence.char && marker[1].length >= fence.length && !marker[2].trim()) fence = null;
      continue;
    }
    if (marker) { fence = { char: marker[1][0], length: marker[1].length }; continue; }
    const heading = line.match(/^###\s+(Paper\s+\d+)\s*$/);
    if (heading) {
      current = { section: heading[1], lines: [] };
      blocks.push(current);
    } else if (/^#{1,3}\s+/.test(line)) {
      current = null;
    } else if (current) {
      current.lines.push(line);
    }
  }
  for (const block of blocks) {
    const text = block.lines.join("\n");
    const title = text.match(/^[ \t]*-[ \t]*\*\*Title:\*\*[ \t]*(.+)$/m)?.[1]?.trim();
    if (!title) continue;
    const value = text.match(/^\s*-\s*\*\*阅读状态[:：]\*\*\s*(.*?)\s*$/m)?.[1]?.trim() || "unread";
    const recommendation = text.match(/^\s*-\s*\*\*Recommendation Type:\*\*\s*(.+)$/m)?.[1]?.trim() || "—";
    papers.push({
      title,
      path: page.file.path.replace(/\.md$/, ""),
      date: page.file.name,
      section: block.section,
      status: aliases[value.toLowerCase()] || "other",
      rawStatus: value,
      recommendation,
    });
  }
}

const total = papers.length;
const count = status => papers.filter(p => p.status === status).length;
const done = count("done");
const other = count("other");
dv.paragraph(`**总数**：${total} 篇 ｜ ` + CONFIG.states.map(st => `${st.emoji} ${st.label} ${count(st.value)}`).join(" ｜ ") + (other ? ` ｜ ⚠️ 未识别状态 ${other}` : ""));
dv.paragraph(`**完成度**：${total ? Math.round(done / total * 100) : 0}%（${done}/${total}）`);

function render(label, emoji, status) {
  const items = papers.filter(p => p.status === status);
  dv.header(3, `${emoji} ${label}（${items.length}）`);
  if (!items.length) { dv.paragraph("（暂无）"); return; }
  const headers = ["论文", "推送日期", "推荐类型"];
  if (status === "other") headers.push("原始状态");
  dv.table(headers, items.map(p => {
    const row = [dv.sectionLink(p.path, p.section, false, p.title), dv.fileLink(p.path, false, p.date), p.recommendation];
    if (status === "other") row.push(p.rawStatus);
    return row;
  }));
}
for (const st of CONFIG.states) render(st.label, st.emoji, st.value);
if (other) render("未识别状态（请修改原日报中的阅读状态）", "⚠️", "other");
if (!total) dv.paragraph("未找到论文：请确认 folder 路径正确，且日报中包含 ### Paper 1 和 - **Title:** 标题。");
```
