"use strict";
const db = window.FILM_DATA;
const $ = id => document.getElementById(id);
const escapeHTML = value => String(value ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
const byId = new Map([...db.films, ...db.people, ...db.companies].map(row => [row.id, row]));
const sources = new Map(db.sources.map(row => [row.id, row]));
let kind = "films", selectedId = "", limit = 50, currentRows = [];
const rowName = row => row.title || row.name || byId.get(row.film_id)?.title || row.id;
const isFilm = row => row.id.startsWith("film-");
function badge(status) {return `<span class="tag ${status === "已核对" ? "verified" : ""}">${escapeHTML(status)}</span>`;}
function nodeButton(row) {return `<button type="button" data-node="${escapeHTML(row.id)}">${escapeHTML(rowName(row))}</button>`;}
function sourceBox(row) {
  const source = sources.get(row.source_id);
  if (!source) return "";
  return `<div class="source"><p><strong>原表位置</strong>　${escapeHTML(source.filename)} · ${escapeHTML(source.sheet)} · 第 ${escapeHTML(row.source_row)} 行${row.source_column ? " · "+escapeHTML(row.source_column)+" 列" : ""}</p><p>文献页码：${escapeHTML(row.source_page || "尚未补充")}　｜　书目与版本：${escapeHTML(source.bibliography || "尚未核实")}</p></div>`;
}
function fields(items) {return `<dl class="fields">${items.map(([label,value])=>`<div class="field"><dt>${escapeHTML(label)}</dt><dd>${escapeHTML(value || "原表未填")}</dd></div>`).join("")}</dl>`;}
function matchingRelations(row) {return db.relations.filter(rel=>rel.from_id === row.id || rel.to_id === row.id);}
function related(row, rel) {return byId.get(rel.from_id === row.id ? rel.to_id : rel.from_id);}
function graph(row, relations) {
  const shown = relations.slice(0,8), count = shown.length;
  if (!count) return `<p class="empty">尚未生成可展示的关系。可以先从原始主创文字核对。</p>`;
  const height = Math.max(200, count * 57 + 32), cy = height / 2;
  const label = (value, max=14) => {const chars=Array.from(value);return escapeHTML(chars.length>max?chars.slice(0,max).join("")+"…":value);};
  const lines = shown.map((rel,i)=>`<path d="M 174 ${cy} C 240 ${cy},240 ${41+i*57},304 ${41+i*57}" stroke="#b7c5b6" fill="none"/>`).join("");
  const nodes = shown.map((rel,i)=>{const other=related(row,rel), y=21+i*57;return `<g class="graph-node" data-node="${escapeHTML(other.id)}" role="button" tabindex="0" aria-label="查看${escapeHTML(rowName(other))}"><title>${escapeHTML(rowName(other))} · ${escapeHTML(rel.type)} · ${escapeHTML(rel.status)}</title><rect x="304" y="${y}" width="218" height="40" rx="3" fill="#fffdf8" stroke="#d7dcd1"/><text x="316" y="${y+17}">${label(rowName(other))}</text><text x="316" y="${y+32}" style="font-size:9px;fill:#68756a">${escapeHTML(rel.type)} · ${escapeHTML(rel.status)}</text></g>`;}).join("");
  return `<svg class="graph" viewBox="0 0 550 ${height}" role="group" aria-label="${escapeHTML(rowName(row))}的局部关系图">${lines}<rect x="14" y="${cy-29}" width="160" height="58" rx="3" fill="#e5ebdf" stroke="#a4b59f"/><text x="25" y="${cy-4}">${label(rowName(row),11)}</text><text x="25" y="${cy+15}" style="font-size:10px;fill:#68756a">当前条目 · ${escapeHTML(row.status)}</text>${nodes}</svg><p class="graph-caption">展示 ${count} / ${relations.length} 条直接关系，点击节点可继续查看。完整关系见下表。</p>`;
}
function show(row, updateHash=true) {
  selectedId = row.id;
  const relations = matchingRelations(row);
  const film = isFilm(row);
  const meta = film ? `${row.year || "年份未填"} · ${row.company_text || "公司未填"}` : `名称候选 · ${relations.length} 条关联记录`;
  let html = `<div class="detail-head"><h2>${escapeHTML(rowName(row))}</h2>${badge(row.status)}</div><p class="subline">${escapeHTML(meta)}<br>固定编号：${escapeHTML(row.id)}</p>`;
  if (film) {
    html += fields([["年份",row.year],["出品公司",row.company_text],["编导／导演",row.director_text],["编剧",row.writer_text],["摄影",row.cinematography_text],["美工",row.art_text],["主演原文",row.cast_text],["其他主创",row.other_text],["备注",row.notes]]);
    if(row.assistant_notes) html += `<h3 class="section-title">补充备注 · 待确认</h3><div class="source">${escapeHTML(row.assistant_notes).replace(/\n/g,"<br>")}</div>`;
    html += `<h3 class="section-title">来源与核对</h3>${sourceBox(row)}`;
    const tasks = db.review_queue.filter(item=>item.film_id===row.id);
    if(tasks.length) html += `<p class="help">核对事项：${tasks.map(task=>`[${escapeHTML(task.status)}] ${escapeHTML(task.reason)}${task.resolution?"（"+escapeHTML(task.resolution)+"）":""}`).join("；")}。</p>`;
  } else html += `<p class="help">${escapeHTML(row.notes)}。相同名称暂归为同一候选，不能据此认定为同一历史人物或机构。</p>`;
  html += `<h3 class="section-title">局部关系</h3>${graph(row,relations)}`;
  if(relations.length) html += `<ul class="relation-list">${relations.map(rel=>`<li>${nodeButton(related(row,rel))}<span>${escapeHTML(rel.type)}</span><small>${escapeHTML(rel.status)} · ${escapeHTML(rel.source_id)} / ${escapeHTML(rel.source_row)}${escapeHTML(rel.source_column)}</small></li>`).join("")}</ul>`;
  const correctionURL = "https://github.com/leohal-hue/chinese-cinema-history/issues/new?template=correction.yml&title=" + encodeURIComponent("[资料核对] " + rowName(row)) + "&record=" + encodeURIComponent(row.id);
  html += `<div class="actions"><a class="action primary" href="${escapeHTML(correctionURL)}" target="_blank" rel="noopener">在 GitHub 提交纠错</a><button id="propose" class="action">下载纠错模板</button><button id="copy-link" class="action">复制条目链接</button></div><p id="action-note" class="help" aria-live="polite">GitHub 纠错由维护者审核；下载模板不会自动提交或修改正式数据。</p>`;
  $("detail").innerHTML=html;
  if(updateHash) history.replaceState(null,"","#"+encodeURIComponent(row.id));
  document.querySelectorAll(".result").forEach(el=>{el.classList.toggle("selected",el.dataset.id===row.id || el.dataset.film===row.id);el.setAttribute("aria-pressed",String(el.classList.contains("selected")));});
  $("propose").onclick=()=>{
    const body=`电影史资料纠错／补充\n\n条目：${rowName(row)}\n编号：${row.id}\n条目链接：${location.href}\n\n需要修改的字段或关系：\n当前内容：\n建议内容：\n依据（文献名称、作者、版本、页码，或网页链接）：\n相关原文：\n补充说明：\n贡献者署名（可选）：\n\n请将此文件交给维护者。此下载不代表修改已提交。\n`;
    const url=URL.createObjectURL(new Blob(["\ufeff"+body],{type:"text/plain;charset=utf-8"}));const a=document.createElement("a");a.href=url;a.download=`纠错-${row.id}.txt`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);$("action-note").textContent="纠错模板已下载。填写后交给维护者；正式资料尚未改变。";
  };
  $("copy-link").onclick=async()=>{try{await navigator.clipboard.writeText(location.href);$("action-note").textContent="条目链接已复制。公开发布后，其他人可通过网站链接访问。";}catch{$("action-note").textContent="请复制浏览器地址栏中的条目链接。";}};
}
function filter() {
  const term=$("search").value.trim().toLocaleLowerCase(), year=$("year").value, status=$("status").value;
  currentRows=db[kind].filter(row=>{
    if(status && row.status!==status)return false;
    if(kind==="films" && year && (year==="unknown"?!!row.year:row.year!==year))return false;
    const haystack=kind==="review_queue"?[rowName(row),row.reason,row.original_value,row.field].join(" "):Object.values(row).join(" ");
    return !term || haystack.toLocaleLowerCase().includes(term);
  });
  $("result-count").textContent=`找到 ${currentRows.length} 条${kind==="review_queue"?"核对事项":"记录"} · 当前显示 ${Math.min(limit,currentRows.length)} 条`;
  $("results").innerHTML=currentRows.slice(0,limit).map(row=>{
    let meta=kind==="films"?`${row.year || "年份未填"} · ${row.company_text || "公司未填"}`:kind==="review_queue"?row.reason:`${matchingRelations(row).length} 条关联记录 · ${row.status}`;
    return `<button class="result ${selectedId===(row.film_id||row.id)?"selected":""}" data-id="${escapeHTML(row.id)}" data-film="${escapeHTML(row.film_id||"")}" aria-pressed="${selectedId===(row.film_id||row.id)}"><span class="result-name">${escapeHTML(rowName(row))}</span><span class="result-meta">${escapeHTML(meta)}</span></button>`;
  }).join("") || `<p class="empty">没有找到匹配记录。试试更短的关键词，或重置筛选条件。原始写法和别名可能尚未统一。</p>`;
  $("more").hidden=currentRows.length<=limit;
}
function switchKind(next) {
  kind=next;limit=50;$("search").value="";$("year").value="";$("status").value="";$("year").disabled=kind!=="films";
  document.querySelectorAll("[data-kind]").forEach(el=>{el.classList.toggle("active",el.dataset.kind===kind);el.setAttribute("aria-pressed",String(el.dataset.kind===kind));});filter();
}
$("stats").innerHTML=[[db.films.length,"影片记录"],[db.people.length,"影人名称候选"],[db.companies.length,"机构名称候选"]].map(([count,label])=>`<div class="stat"><strong>${count}</strong><span>${label}</span></div>`).join("");
[...new Set(db.films.map(row=>row.year).filter(Boolean))].sort().forEach(year=>{const option=document.createElement("option");option.value=year;option.textContent=year;$("year").append(option);});
document.querySelectorAll("[data-kind]").forEach(el=>el.onclick=()=>switchKind(el.dataset.kind));
["search","year","status"].forEach(id=>$(id).addEventListener(id==="search"?"input":"change",()=>{limit=50;filter();}));
$("reset").onclick=()=>switchKind(kind);
$("more").onclick=()=>{limit+=50;filter();};
$("results").onclick=event=>{const button=event.target.closest("[data-id]");if(!button)return;const row=byId.get(button.dataset.film||button.dataset.id);if(row){show(row);if(innerWidth<=850)$("detail").scrollIntoView({block:"start"});}};
function navigateNode(event) {const target=event.target.closest("[data-node]");if(!target)return;const row=byId.get(target.dataset.node);if(row){switchKind(isFilm(row)?"films":row.id.startsWith("person-")?"people":"companies");show(row);}}
$("detail").onclick=navigateNode;
$("detail").onkeydown=event=>{if((event.key==="Enter" || event.key===" ") && event.target.closest("g[data-node]")){event.preventDefault();navigateNode(event);}};
function fromHash() {let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}const row=byId.get(id);if(row){switchKind(isFilm(row)?"films":id.startsWith("person-")?"people":"companies");show(row,false);}else{filter();show(db.films[0],false);}}
window.addEventListener("hashchange",fromHash);fromHash();
