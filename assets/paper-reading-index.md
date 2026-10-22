---
type: moc
---

# 📚 论文阅读索引

> 日报每篇论文可勾选“进行精读”，下表同步显示是否精读，勾选仅记录选择。实际精读笔记勾选属性 `template` 后归入“已读”；未勾选时按笔记 `status` 显示，没有笔记则沿用日报状态。真正的模板按 `type: literature-template` 排除。同一来源只计一次，面板不回写日报或笔记。

```dataviewjs
const CONFIG = {
  folder: "Research Radar/Daily Papers",
  noteFolder: "Research Radar/Note",
};
const aliases = {unread:"unread",unreading:"unread","未读":"unread",reading:"reading","阅读中":"reading",done:"done","已读":"done","已完成":"done"};
const states = [{value:"unread",label:"未读",emoji:"📥"},{value:"reading",label:"阅读中",emoji:"📖"},{value:"done",label:"已读",emoji:"✅"},{value:"other",label:"待核对",emoji:"⚠️"}];
const checked = value => value===true || String(value).trim().toLowerCase()==="true";
const dateText = value => value?.toFormat ? value.toFormat("yyyy-MM-dd") : String(value ?? "").slice(0,10);
const canonical = value => aliases[String(Array.isArray(value) ? value[0] : value ?? "unread").trim().toLowerCase()] || "other";
const normalize = value => String(value ?? "").normalize("NFKC").toLowerCase().replace(/[^\p{L}\p{N}]/gu,"");
const withoutMd = value => value.replace(/\.md$/i,"");
const uri = (value, route) => String(value ?? "").match(new RegExp("zotero://"+route+"/(?:library|groups/\\d+)/items/[A-Z0-9]{8}(?![A-Z0-9])"))?.[0];
const papers = new Map();
for (const page of dv.pages('"'+CONFIG.folder+'"')) {
  const raw = await dv.io.load(page.file.path);
  if (!raw) continue;
  const blocks=[]; let current=null, fence=null;
  for (const line of raw.split(/\r?\n/)) {
    const marker=line.match(/^\s{0,3}(`{3,}|~{3,})(.*)$/);
    if (fence) {
      if (marker && marker[1][0]===fence.char && marker[1].length>=fence.length && !marker[2].trim()) fence=null;
      continue;
    }
    if (marker) {fence={char:marker[1][0],length:marker[1].length};continue;}
    const heading=line.match(/^###\s+Paper\s+(\d+)\s*$/);
    if (heading) {current={number:Number(heading[1]),lines:[]};blocks.push(current);}
    else if (/^#{1,3}\s+/.test(line)) current=null;
    else if (current) current.lines.push(line);
  }
  for (const block of blocks) {
    const text=block.lines.join("\n");
    const field=name=>text.match(new RegExp("^-[ \\t]+\\*\\*"+name+"[:：]\\*\\*[ \\t]*(.*)$","m"))?.[1]?.trim();
    const title=field("Title"); if (!title) continue;
    const sourceDate=page.file.name;
    const id=sourceDate+":"+block.number;
    const decision=text.match(/^\s*-\s*\[([xX ])\][ \t]*进行精读[ \t]*$/m);
    const row={id,title,date:sourceDate,number:block.number,daily:withoutMd(page.file.path),recommendation:field("Recommendation Type")||"—",status:canonical(field("阅读状态")),deepRead:decision?decision[1].toLowerCase()==="x":null,notes:[],item:uri(field("Zotero 文献"),"select"),pdf:uri(field("Zotero PDF"),"open-pdf")};
    if (papers.has(id)) {papers.get(id).conflict="日报来源重复";papers.get(id).status="other";}
    else papers.set(id,row);
  }
}
for (const note of dv.pages('"'+CONFIG.noteFolder+'"')) {
  if (note.type!=="literature") continue;
  const day=dateText(note.source_date), number=Number(note.paper_number);
  const hasSource=/^\d{4}-\d{2}-\d{2}$/.test(day) && Number.isInteger(number) && number>0;
  const id=hasSource ? day+":"+number : "note:"+note.file.path;
  let row=papers.get(id);
  if (!row) {
    row={id,title:note.title||note.file.name,date:hasSource?day:"—",number:hasSource?number:null,daily:null,recommendation:"精读笔记",status:"unread",notes:[]};
    papers.set(id,row);
  }
  row.notes.push(note);
  if (row.notes.length>1) {row.conflict="同一来源对应多个精读笔记";row.status="other";}
  else if (row.daily && normalize(note.title)!==normalize(row.title)) {row.conflict="精读题名与日报不一致";row.status="other";}
  else if (!row.conflict) {
    row.status=checked(note.template)?"done":canonical(note.status);
    if (row.deepRead==null) row.deepRead=true;
    row.item=uri(note.zotero_item_url,"select")||row.item;
    row.pdf=uri(note.zotero_pdf_url,"open-pdf")||row.pdf;
  }
}
const rows=[...papers.values()].sort((a,b)=>b.date.localeCompare(a.date)||(a.number??0)-(b.number??0));
const count=value=>rows.filter(p=>p.status===value).length;
dv.paragraph(`**共 ${rows.length} 篇** ｜ `+states.map(s=>`${s.emoji} ${s.label} ${count(s.value)}`).join(" ｜ ")+` ｜ 🔬 已选精读 ${rows.filter(p=>p.deepRead===true).length}`);
dv.paragraph(`**完成度**：${rows.length?Math.round(count("done")/rows.length*100):0}%（${count("done")}/${rows.length}）`);
for (const state of states) {
  const items=rows.filter(p=>p.status===state.value);
  if (!items.length && state.value==="other") continue;
  dv.header(3,`${state.emoji} ${state.label}（${items.length}）`);
  if (!items.length) {dv.paragraph("（暂无）");continue;}
  dv.table(["论文","推荐来源","精读笔记","Zotero","说明","是否精读"],items.map(p=>[
    p.daily?dv.sectionLink(p.daily,`Paper ${p.number}`,false,p.title):dv.fileLink(withoutMd(p.notes[0].file.path),false,p.title),
    p.daily?dv.sectionLink(p.daily,`Paper ${p.number}`,false,`${p.date} · Paper ${p.number}`):"—",
    p.notes.length?p.notes.map(n=>dv.fileLink(withoutMd(n.file.path),false,"精读笔记")):(p.deepRead===true?"待生成":"—"),
    [p.item?`[文献](${p.item})`:null,p.pdf?`[PDF](${p.pdf})`:null].filter(Boolean).join(" · ")||"待核验",
    p.conflict||p.recommendation,
    p.deepRead===true?"是":p.deepRead===false?"否":"未选择",
  ]));
}
if (!rows.length) dv.paragraph("尚无论文：请检查 CONFIG 中的库相对路径、日报字段及 Note 的 type: literature。");
```
