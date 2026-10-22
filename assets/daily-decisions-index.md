---
type: moc
---

# 📡 Daily Papers 索引

## 🗂 按阅读决定分类

```dataviewjs
const CONFIG = {
  folder: "Research Radar/Daily Papers",   // 每日笔记所在文件夹
  jsonPath: "Research Radar/Database/recommended.json",  // 论文 JSON（可选）
  typeField: "",                                            // 可选：留空 = 不按 type 过滤
};

const CATEGORIES = [
  { label: "值得进一步阅读", emoji: "✅", match: "值得进一步阅读" },
  { label: "加入待处理清单", emoji: "📋", match: "加入待处理清单" },
  { label: "暂不处理", emoji: "⏸️", match: "暂不处理" },
  { label: "需要先查看相关论文", emoji: "🔍", match: "需要先查看相关论文" },
];

let typeMap = {};
try {
  const jraw = await dv.io.load(CONFIG.jsonPath);
  const jpapers = jraw ? JSON.parse(jraw) : [];
  for (const p of jpapers) typeMap[p.title] = p.recommend_type;
} catch (e) {}

let pages = dv.pages('"' + CONFIG.folder + '"');
if (CONFIG.typeField) pages = pages.where(p => p.type === CONFIG.typeField);
pages = pages.sort(p => p.file.name, "desc");

const allPapers = [];
for (const page of pages) {
  const raw = await dv.io.load(page.file.path);
  if (!raw) continue;
  const pathNoMd = page.file.path.replace(/\.md$/, "");
  const date = page.file.name;

  const blocks = [];
  const lines = raw.split("\n");
  let current = null;
  for (const line of lines) {
    const h = line.match(/^###\s+(Paper\s+\d+)\s*$/);
    if (h) {
      current = { section: h[1], text: "" };
      blocks.push(current);
      continue;
    }
    if (current && /^##\s+/.test(line)) {
      current = null;
      continue;
    }
    if (current) current.text += line + "\n";
  }

  for (const b of blocks) {
    const tm = b.text.match(/^[ \t]*-[ \t]*\*\*Title:\*\*[ \t]*(.+)$/m);
    const title = tm ? tm[1].trim() : "";
    if (!title) continue;
    const decisions = [];
    const re = /^\s*-\s*\[([xX ])\]\s*(.+)$/gm;
    let m;
    while ((m = re.exec(b.text))) {
      if (m[1].toLowerCase() === "x") {
        const t = m[2].trim();
        const cat = CATEGORIES.find(c => t.startsWith(c.match));
        if (cat) decisions.push(cat.label);
      }
    }
    allPapers.push({
      date,
      pathNoMd,
      section: b.section,
      title: title.replace(/\|/g, "｜"),
      decisions,
      type: typeMap[title] === "highly_relevant" ? "🔴 强相关"
          : typeMap[title] === "trending" ? "🔥 热点" : "—",
    });
  }
}

const groups = { "未决定": [] };
for (const c of CATEGORIES) groups[c.label] = [];
for (const p of allPapers) {
  if (p.decisions.length === 0) groups["未决定"].push(p);
  else for (const d of p.decisions) groups[d].push(p);
}

dv.paragraph(
  `**共 ${allPapers.length} 篇** ｜ ` +
  CATEGORIES.map(c => `${c.emoji} ${c.label} ${groups[c.label].length}`).join(" ｜ ") +
  ` ｜ ❔ 未决定 ${groups["未决定"].length}`
);

const render = (label, emoji) => {
  const items = groups[label];
  dv.header(3, `${emoji} ${label}（${items.length}）`);
  if (items.length) {
    dv.table(
      ["日期", "论文", "类型"],
      items.map(p => [
        `[[${p.pathNoMd}|${p.date}]]`,
        `[[${p.pathNoMd}#${p.section}|${p.title}]]`,
        p.type
      ])
    );
  } else {
    dv.paragraph("（暂无）");
  }
};

for (const c of CATEGORIES) render(c.label, c.emoji);
render("未决定", "❔");
```
