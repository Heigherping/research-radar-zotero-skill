const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
const source=fs.readFileSync(path.join(__dirname,'../assets/paper-reading-index.md'),'utf8');
const code=source.match(/```dataviewjs\s*([\s\S]*?)```/)[1];
const daily=['# Daily',...[1,2,3].flatMap(n=>[`### Paper ${n}`,`- **Title:** Sample ${n}`,'- **阅读状态:** unread','- **Zotero 文献:** [item](zotero://select/library/items/PARENT01)','- **Zotero PDF:** [PDF](zotero://open-pdf/library/items/PDFKEY01)']),'## Summary'].join('\n');
const page={file:{path:'Research Radar/Daily Papers/2026-10-22.md',name:'2026-10-22'}};
const note=(number,status='reading',file='note.md')=>({type:'literature',source_date:'2026-10-22',paper_number:number,title:`Sample ${number}`,status,file:{path:'Research Radar/Note/'+file,name:file}});
async function render(notes,raw=daily) {
  const paragraphs=[],headers=[],tables=[];
  const dv={pages:q=>q.includes('Daily Papers')?[page]:notes,io:{load:async()=>raw},
    paragraph:x=>paragraphs.push(x),header:(level,x)=>headers.push(x),table:(cols,rows)=>tables.push({cols,rows}),
    sectionLink:(p,s,e,t)=>({path:p,section:s,title:t}),fileLink:(p,e,t)=>({path:p,title:t})};
  await new AsyncFunction('dv',code)(dv);
  return {paragraphs,headers,rows:tables.flatMap(t=>t.rows)};
}
(async()=>{
  let r=await render([]);
  assert.equal(r.rows.length,3);assert(r.headers.includes('📥 未读（3）'));
  r=await render([note(2)]);
  assert.equal(r.rows.length,3);assert(r.headers.includes('📖 阅读中（1）'));assert(r.headers.includes('📥 未读（2）'));
  assert.equal(r.rows.find(row=>row[0].title==='Sample 2')[2][0].path,'Research Radar/Note/note');
  assert(r.rows[0][3].includes('zotero://select/library/items/'));
  r=await render([note(2,'done')]);
  assert(r.headers.includes('✅ 已完成（1）'));assert(r.paragraphs[1].includes('33%'));
  r=await render([{type:'literature-template',template:true,file:{path:'template.md'}},note(2,'done')]);
  assert.equal(r.rows.length,3);
  r=await render([note(2),note(2,'done','duplicate.md')]);
  assert.equal(r.rows.length,3);assert(r.headers.includes('⚠️ 待核对（1）'));assert(r.rows.some(row=>row[4].includes('多个')));
  r=await render([note(8,'done','orphan.md')]);assert.equal(r.rows.length,4);
  r=await render([{...note(2),title:'Wrong paper'}]);assert(r.headers.includes('⚠️ 待核对（1）'));
  r=await render([note(2,'unexpected')]);assert(r.headers.includes('⚠️ 待核对（1）'));
  r=await render([], '### Paper 1\n- **Title:**\n- **Zotero 文献:** Missing');assert.equal(r.rows.length,0);
  r=await render([], '```md\n### Paper 8\n- **Title:** Fake\n```\n'+daily);assert.equal(r.rows.length,3);
  console.log('Reading index: 10 scenarios passed (merge, status changes, template exclusion, conflicts, orphan, empty title, fenced examples)');
})().catch(e=>{console.error(e);process.exitCode=1;});
