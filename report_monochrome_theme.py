from __future__ import annotations

import argparse
import os
from pathlib import Path
import re

THEME_MARKER = "MCPT_REPORT_SHELL_V4"

REPORT_SHELL_CSS = r'''
/* MCPT_REPORT_SHELL_V4 */
:root {
  color-scheme: dark;
  --bg:#070707 !important; --panel:#111113 !important;
  --panel2:#18181b !important; --panel-2:#18181b !important;
  --line:#343436 !important; --border:#343436 !important;
  --text:#f1efeb !important; --muted:#9c968e !important;
  --accent:#c6a06a !important; --silver:#c8c5bf !important; --good:#9eae8f !important;
  --bad:#c98378 !important; --warning:#c9a667 !important;
  --sidebar-width:304px;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;background:var(--bg)!important}
body{
  margin:0!important;color:var(--text)!important;background-color:var(--bg)!important;
  background-image:linear-gradient(rgba(255,255,255,.026) 1px,transparent 1px),
  linear-gradient(90deg,rgba(255,255,255,.026) 1px,transparent 1px)!important;
  background-size:72px 72px!important;background-attachment:fixed!important;
}
body.mcpt-shell-ready{padding-left:var(--sidebar-width)!important}
body.mcpt-sidebar-hidden{padding-left:0!important}
body.mcpt-shell-ready>main,body.mcpt-shell-ready>.page,body.mcpt-shell-ready>.container,.mcpt-report-content{
  width:min(1540px,calc(100vw - var(--sidebar-width) - 40px))!important;
  max-width:none!important;margin-left:auto!important;margin-right:auto!important;
}
body.mcpt-sidebar-hidden>main,body.mcpt-sidebar-hidden>.page,body.mcpt-sidebar-hidden>.container,
body.mcpt-sidebar-hidden .mcpt-report-content{width:min(1540px,calc(100vw - 40px))!important}
#mcpt-report-sidebar{
  position:fixed;inset:0 auto 0 0;z-index:1000;width:var(--sidebar-width);
  display:flex;flex-direction:column;background:rgba(8,8,9,.99);
  border-right:1px solid var(--line);box-shadow:16px 0 42px rgba(0,0,0,.24);
  transition:transform .16s ease;
}
body.mcpt-sidebar-hidden #mcpt-report-sidebar{transform:translateX(-100%)}
.mcpt-sidebar-head{padding:18px 16px 14px;border-bottom:1px solid var(--line)}
.mcpt-sidebar-kicker{color:var(--accent);font-size:11px;font-weight:850;letter-spacing:.14em;text-transform:uppercase}
.mcpt-sidebar-title{margin-top:6px;color:var(--text);font-size:15px;font-weight:800;line-height:1.3}
.mcpt-sidebar-actions{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;margin-top:13px}
.mcpt-sidebar-actions a,.mcpt-sidebar-actions button,#mcpt-menu-open{
  border:1px solid var(--line)!important;border-radius:8px!important;background:var(--panel)!important;
  color:var(--text)!important;padding:8px 10px!important;font:inherit!important;text-decoration:none!important;cursor:pointer;
}
.mcpt-sidebar-actions a:hover,.mcpt-sidebar-actions button:hover,#mcpt-menu-open:hover{border-color:var(--accent)!important}
.mcpt-sidebar-nav{min-height:0;overflow-y:auto;padding:12px 10px 24px;scrollbar-width:thin}
.mcpt-overview-link,.mcpt-menu-parent,.mcpt-menu-child{
  width:100%;display:block;border:0!important;border-radius:0!important;background:transparent!important;
  text-align:left;text-decoration:none!important;cursor:pointer;
}
.mcpt-overview-link,.mcpt-menu-parent{
  color:var(--text)!important;padding:10px 8px!important;font-size:13px!important;font-weight:800!important;line-height:1.35;
}
.mcpt-overview-link:hover,.mcpt-overview-link.mcpt-active-parent,
.mcpt-menu-parent:hover,.mcpt-menu-parent.mcpt-active-parent{color:var(--accent)!important}
.mcpt-menu-children{display:block;margin:0 0 7px;padding:0 0 2px 11px}
.mcpt-menu-child{position:relative;color:var(--muted)!important;padding:7px 8px 7px 14px!important;font-size:12px!important;line-height:1.35}
.mcpt-menu-child::before{content:"";position:absolute;left:0;top:5px;bottom:5px;width:2px;border-radius:2px;background:transparent}
.mcpt-menu-child:hover,.mcpt-menu-child.mcpt-active{color:var(--text)!important}
.mcpt-menu-child.mcpt-active::before{background:var(--accent)}
#mcpt-menu-open{position:fixed;left:12px;top:12px;z-index:1001;display:none}
body.mcpt-sidebar-hidden #mcpt-menu-open{display:block}
.report-nav,nav.report-nav,.sticky-nav,.top-nav,body>main>nav{display:none!important}
a{color:var(--accent)}
h1,h2,h3,h4,.section-title,.section-header h2{color:var(--text)!important}
.eyebrow,.kicker,.section-kicker,.exp-id,.group-heading span,.section-accent,.status{color:var(--accent)!important}
.panel,.metric-card,.comparison-card,.notice,.details-card,.chart-card,.card,.summary-card,.metric-tile,
.callout,.strategy,.explanation,.strategy-rule-card,.strategy-example,.strategy-distinction,.metadata>div,.stat,
.research-group,.experiment{
  background:var(--panel)!important;border-color:var(--line)!important;box-shadow:none!important;
}
.callout,.notice,.strategy-example,.lineage-flow{border-left-color:var(--accent)!important}
.explanation,.strategy{padding:14px 16px!important}
.muted,.subtitle,.section-kicker,.metric-detail,.parameter-name,.comparison-heading,.note,.lead{color:var(--muted)!important}
.metric-label,.metric-name,.kpi-label,.stat span,.mcpt-metric-label,.mcpt-record-grid dt,
.mcpt-matrix-table th:first-child,.strategy-rule-card h3,.strategy-rule-card h4,
.strategy-rule-grid>div>h3,.strategy-rule-grid>div>h4,.strategy-rule-grid>div>strong:first-child,
.rule-card h3,.rule-card h4,.explanation>h3:first-child{color:var(--accent)!important}
.strategy>h3,.mcpt-matrix-table thead th:not(:first-child){color:var(--silver)!important}
.grid.mcpt-stat-grid{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:12px!important;margin:14px 0 20px!important}
.grid.mcpt-stat-grid .stat{min-height:0!important;padding:12px 14px!important;margin:0!important}
.grid.mcpt-stat-grid .stat strong{font-size:1.15rem!important}
.grid.mcpt-chart-grid,.chart-grid{display:grid!important;grid-template-columns:1fr!important;gap:18px!important}
img.chart,.chart-card img,section>img{display:block!important;width:100%!important;height:auto!important;margin:16px 0!important}
button,.button,input,select,textarea{background:var(--panel)!important;color:var(--text)!important;border-color:var(--line)!important}
button:hover,.button:hover{border-color:var(--accent)!important}
.table-shell,.table-wrap,.table-scroll{width:100%!important;max-width:100%!important;overflow:visible!important;background:transparent!important;border-color:var(--line)!important}
table,.data-table,.metric-table,.comparison-table,.artifact-table{width:100%!important;min-width:0!important;table-layout:fixed!important;background:var(--panel)!important}
thead th,.data-table thead th{position:static!important;background:var(--panel2)!important;color:var(--text)!important;border-color:var(--line)!important}
th,td,.data-table th,.data-table td,.strategy-parameter-table th,.strategy-parameter-table td{
  min-width:0!important;max-width:none!important;white-space:normal!important;overflow-wrap:anywhere!important;
  word-break:normal!important;border-color:var(--line)!important;
}
tbody tr:hover,.data-table tbody tr:hover{background:rgba(198,160,106,.07)!important}
.mcpt-wide-source{display:none!important}
.mcpt-compare-shell{margin:12px 0 20px}
.mcpt-compare-toolbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 10px}
.mcpt-compare-count{margin-left:auto;color:var(--muted);font-size:12px}
.mcpt-group-list{display:grid;gap:10px}
.mcpt-record-group{border:1px solid var(--line);border-radius:10px;background:var(--panel);overflow:hidden}
.mcpt-record-group>summary{cursor:pointer;list-style:none;padding:11px 13px;color:var(--text);font-weight:760}
.mcpt-record-group>summary::-webkit-details-marker{display:none}
.mcpt-group-body{border-top:1px solid var(--line);padding:10px}
.mcpt-matrix-wrap{width:100%;overflow:visible}
.mcpt-matrix-table{width:100%!important;table-layout:fixed!important}
.mcpt-matrix-table th:first-child,.mcpt-matrix-table td:first-child{width:30%}
.mcpt-matrix-table th,.mcpt-matrix-table td{text-align:left!important}
.mcpt-record-list{display:grid;gap:9px}
.mcpt-data-record{border:1px solid var(--line);border-radius:9px;background:var(--panel);overflow:hidden}
.mcpt-data-record>summary{cursor:pointer;list-style:none;padding:11px 13px;color:var(--text);font-weight:740}
.mcpt-data-record>summary::-webkit-details-marker{display:none}
.mcpt-record-grid{display:grid;grid-template-columns:minmax(180px,32%) minmax(0,1fr);margin:0;border-top:1px solid var(--line)}
.mcpt-record-grid dt,.mcpt-record-grid dd{margin:0;padding:8px 11px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}
.mcpt-record-grid dt{background:var(--panel2);font-weight:650}.mcpt-record-grid dd{color:var(--text)}
code,pre{background:var(--panel2)!important;border-color:var(--line)!important}
hr{border-color:var(--line)!important}
@media(max-width:980px){.grid.mcpt-stat-grid{grid-template-columns:1fr!important}}
@media(max-width:900px){
  body.mcpt-shell-ready{padding-left:0!important}
  #mcpt-report-sidebar{width:min(88vw,330px)}
  body.mcpt-shell-ready:not(.mcpt-sidebar-hidden) #mcpt-report-sidebar{transform:translateX(0)}
  body.mcpt-sidebar-hidden #mcpt-report-sidebar{transform:translateX(-100%)}
  body.mcpt-shell-ready>main,body.mcpt-shell-ready>.page,body.mcpt-shell-ready>.container,.mcpt-report-content{
    width:100%!important;padding-left:15px!important;padding-right:15px!important;
  }
  #mcpt-menu-open{display:block}.mcpt-record-grid{grid-template-columns:1fr}
  .mcpt-matrix-table th:first-child,.mcpt-matrix-table td:first-child{width:38%}
}
@media print{#mcpt-report-sidebar,#mcpt-menu-open,.mcpt-compare-toolbar{display:none!important}body.mcpt-shell-ready{padding-left:0!important}}
'''

REPORT_SHELL_JS = r'''
/* MCPT_REPORT_SHELL_V4 */
(()=>{
"use strict";
const marker="MCPT_REPORT_SHELL_V4";
const q=(s,r=document)=>r.querySelector(s),qa=(s,r=document)=>Array.from(r.querySelectorAll(s));
const slug=t=>String(t||"section").trim().toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"")||"section";
const esc=v=>String(v??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
function root(){return q(".page")||q("main")||q(".container")||document.body}
function dashboardHref(){const m=q('meta[name="mcpt-dashboard-href"]');return m?m.content:"../research_dashboard/index.html"}
function classifyGrids(){qa(".grid").forEach(g=>{if(q(".stat",g))g.classList.add("mcpt-stat-grid");if(q("img",g))g.classList.add("mcpt-chart-grid")})}
function buildSidebar(){
 if(q("#mcpt-report-sidebar"))return;
 const content=root();if(content!==document.body)content.classList.add("mcpt-report-content");
 const used=new Set();const headings=qa("h1,h2,h3").filter(h=>!h.closest("#mcpt-report-sidebar")&&h.textContent.trim());
 headings.forEach(h=>{if(!h.id){let b="mcpt-"+slug(h.textContent),c=b,n=2;while(used.has(c)||document.getElementById(c))c=b+"-"+n++;h.id=c}used.add(h.id)});
 const h1=headings.find(h=>h.tagName==="H1")||null,h2s=headings.filter(h=>h.tagName==="H2");
 const side=document.createElement("aside");side.id="mcpt-report-sidebar";
 const head=document.createElement("div");head.className="mcpt-sidebar-head";
 head.innerHTML='<div class="mcpt-sidebar-kicker">Report navigation</div><div class="mcpt-sidebar-title"></div><div class="mcpt-sidebar-actions"><a href="'+dashboardHref()+'">Research dashboard</a><button type="button">Hide</button></div>';
 q(".mcpt-sidebar-title",head).textContent=h1?h1.textContent.trim():document.title;
 const nav=document.createElement("nav");nav.className="mcpt-sidebar-nav";
 const item=new Map(),groupFor=new Map();
 if(h1){const a=document.createElement("a");a.className="mcpt-overview-link";a.href="#"+h1.id;a.textContent="Report overview";nav.append(a);item.set(h1,a)}
 function openGroup(_target){}
 function setActive(h){qa(".mcpt-active,.mcpt-active-parent",nav).forEach(x=>x.classList.remove("mcpt-active","mcpt-active-parent"));const i=item.get(h);if(!i)return;if(i.classList.contains("mcpt-menu-child")){i.classList.add("mcpt-active");const g=groupFor.get(h);if(g){openGroup(g);q(".mcpt-menu-parent",g)?.classList.add("mcpt-active-parent")}}else{i.classList.add("mcpt-active-parent");const g=groupFor.get(h);if(g)openGroup(g)}}
 h2s.forEach((h2,index)=>{const next=h2s[index+1]||null;const children=headings.filter(h=>h.tagName==="H3"&&(h2.compareDocumentPosition(h)&Node.DOCUMENT_POSITION_FOLLOWING)&&(!next||(h.compareDocumentPosition(next)&Node.DOCUMENT_POSITION_FOLLOWING)));
  const g=document.createElement("div");g.className="mcpt-menu-group";const p=document.createElement("button");p.type="button";p.className="mcpt-menu-parent";p.textContent=h2.textContent.trim();const box=document.createElement("div");box.className="mcpt-menu-children";
  children.forEach(h3=>{const a=document.createElement("a");a.className="mcpt-menu-child";a.href="#"+h3.id;a.textContent=h3.textContent.trim();box.append(a);item.set(h3,a);groupFor.set(h3,g)});
  p.addEventListener("click",()=>{openGroup(g);h2.scrollIntoView({behavior:"smooth",block:"start"});setActive(h2)});g.append(p);if(children.length)g.append(box);nav.append(g);item.set(h2,p);groupFor.set(h2,g)});
 nav.addEventListener("click",e=>{const a=e.target.closest("a");if(!a||!a.hash)return;const target=q(a.hash);if(!target)return;e.preventDefault();target.scrollIntoView({behavior:"smooth",block:"start"});setActive(target);if(matchMedia("(max-width:900px)").matches)setHidden(true)});
 side.append(head,nav);document.body.prepend(side);const open=document.createElement("button");open.id="mcpt-menu-open";open.type="button";open.textContent="Menu";document.body.prepend(open);
 const key="mcpt-report-sidebar:"+location.pathname;function setHidden(v){document.body.classList.toggle("mcpt-sidebar-hidden",v);try{localStorage.setItem(key,v?"hidden":"shown")}catch(_){}}
 let hidden=false;try{hidden=localStorage.getItem(key)==="hidden"}catch(_){}document.body.classList.add("mcpt-shell-ready");setHidden(hidden);q("button",head).addEventListener("click",()=>setHidden(true));open.addEventListener("click",()=>setHidden(false));
 const observed=[h1,...h2s,...headings.filter(h=>h.tagName==="H3")].filter(Boolean);if("IntersectionObserver"in window){const visible=new Map();const obs=new IntersectionObserver(entries=>{entries.forEach(e=>e.isIntersecting?visible.set(e.target,e.boundingClientRect.top):visible.delete(e.target));if(!visible.size)return;const active=Array.from(visible.entries()).sort((a,b)=>a[1]-b[1])[0][0];setActive(active)},{rootMargin:"-10% 0px -78% 0px",threshold:[0,1]});observed.forEach(h=>obs.observe(h))}if(h1)setActive(h1)
}
const text=c=>(c?c.textContent:"").trim()||"—";
function tableData(table){let heads=qa("thead th",table).map(text);if(!heads.length){const first=q("tr",table);heads=first?Array.from(first.children).map((c,i)=>text(c)==="—"?"Column "+(i+1):text(c)):[]}let rows=qa("tbody tr",table);if(!rows.length){rows=qa("tr",table);if(rows.length>1)rows=rows.slice(1)}const records=rows.map(r=>heads.map((h,i)=>({header:h,text:text(r.children[i]),html:r.children[i]?r.children[i].innerHTML:"—"})));return{heads,records}}
function titleOf(record,index){for(const name of["strategy","candidate","signal candidate id","candidate id","sizing id","series id","pair id","family id"]){const f=record.find(x=>x.header.toLowerCase()===name);if(f&&f.text!=="—")return f.text}return record.filter(x=>x.text!=="—").slice(0,2).map(x=>x.text).join(" · ")||"Record "+(index+1)}
function identityIndex(heads,records){for(const name of["strategy","candidate","signal candidate id","candidate id","sizing id","series id","pair id","family id"]){const i=heads.findIndex(h=>h.toLowerCase()===name);if(i>=0&&records.some(r=>r[i]&&r[i].text!=="?"))return i}return-1}
function groupIndex(heads,records){if(records.length<=3)return-1;const pr=new Map([["signal candidate id",60],["family id",50],["minimum drive fraction",45],["period",35],["symbol",10]]);let best={i:-1,s:-1e9};heads.forEach((h,i)=>{const vals=records.map(r=>r[i].text);if(vals.some(v=>v==="—"))return;const counts=new Map();vals.forEach(v=>counts.set(v,(counts.get(v)||0)+1));if(counts.size<2||counts.size>=records.length)return;const sizes=Array.from(counts.values()),max=Math.max(...sizes),min=Math.min(...sizes);const score=(max<=3?100:max<=6?25:0)+(max-min<=1?15:0)+(pr.get(h.toLowerCase())||0)-counts.size;if(score>best.s)best={i,s:score}});return best.i}
function matrix(heads,records,excluded=new Set()){const hidden=new Set(excluded),identity=identityIndex(heads,records);if(identity>=0)hidden.add(identity);const wrap=document.createElement("div");wrap.className="mcpt-matrix-wrap";const table=document.createElement("table");table.className="mcpt-matrix-table";const thead=document.createElement("thead"),hr=document.createElement("tr"),mh=document.createElement("th");mh.textContent="";hr.append(mh);records.forEach((r,i)=>{const th=document.createElement("th");th.textContent=titleOf(r,i);hr.append(th)});thead.append(hr);const tbody=document.createElement("tbody");heads.forEach((h,fi)=>{if(hidden.has(fi))return;const tr=document.createElement("tr"),label=document.createElement("th");label.className="mcpt-metric-label";label.textContent=h;tr.append(label);records.forEach(r=>{const td=document.createElement("td");td.innerHTML=r[fi].html||"—";tr.append(td)});tbody.append(tr)});table.append(thead,tbody);wrap.append(table);return wrap}
function cards(records){const list=document.createElement("div");list.className="mcpt-record-list";records.forEach((r,i)=>{const d=document.createElement("details");d.className="mcpt-data-record";const s=document.createElement("summary");s.textContent=titleOf(r,i);const dl=document.createElement("dl");dl.className="mcpt-record-grid";r.forEach(f=>{const dt=document.createElement("dt"),dd=document.createElement("dd");dt.textContent=f.header;dd.innerHTML=f.html||"—";dl.append(dt,dd)});d.append(s,dl);list.append(d)});return list}
function compareDoc(title,heads,records){const identity=identityIndex(heads,records),sections=[[/id|name|strategy|candidate|signal|sizing|symbol|family|mode|type|status|period/i,"Identity and setup"],[/trade|signal count|holding|time|duration|skip|contract/i,"Trade activity and timing"],[/profit|win|average trade|payoff|gross|net/i,"Profit and trade quality"],[/risk|drawdown|loss|adverse|mfe|mae|underwater/i,"Risk and drawdown"],[/year|month|bootstrap|mcpt|walk|cost|slippage|ratio|coefficient|percentile|reliability|context/i,"Robustness and context"]],used=new Set(identity>=0?[identity]:[]),blocks=[];for(const[re,name]of sections){const idx=heads.map((h,i)=>re.test(h)&&!used.has(i)?i:-1).filter(i=>i>=0);idx.forEach(i=>used.add(i));if(idx.length)blocks.push([name,idx])}const rest=heads.map((_,i)=>used.has(i)?-1:i).filter(i=>i>=0);if(rest.length)blocks.push(["Other measurements",rest]);const html=blocks.map(([name,idx])=>{const hs=records.map((r,i)=>"<th>"+esc(titleOf(r,i))+"</th>").join("");const body=idx.map(fi=>"<tr><th>"+esc(heads[fi])+"</th>"+records.map(r=>"<td>"+(r[fi].html||"—")+"</td>").join("")+"</tr>").join("");return"<section><h2>"+esc(name)+"</h2><table><thead><tr><th></th>"+hs+"</tr></thead><tbody>"+body+"</tbody></table></section>"}).join("");return'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'</title><style>:root{color-scheme:dark;--bg:#070707;--panel:#111113;--panel2:#18181b;--text:#f1efeb;--line:#343436;--accent:#c6a06a;--silver:#c8c5bf}*{box-sizing:border-box}body{margin:0;padding:28px;background:#070707;color:var(--text);font:14px/1.5 Inter,Segoe UI,Arial,sans-serif}main{width:min(1800px,100%);margin:auto}section{margin:0 0 20px;padding:18px;border:1px solid var(--line);border-radius:12px;background:var(--panel)}table{width:100%;border-collapse:collapse;table-layout:fixed}th,td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;white-space:normal;overflow-wrap:anywhere;vertical-align:top}thead th{background:var(--panel2)}thead th:not(:first-child){color:var(--silver)}tbody th{width:28%;color:var(--accent);background:var(--panel2)}</style></head><body><main><h1>'+esc(title)+'</h1>'+html+'</main></body></html>'}
function openCompare(title,heads,records){const pop=window.open("","_blank");if(!pop){alert("The comparison tab was blocked by the browser.");return}const doc=compareDoc(title,heads,records);try{pop.document.open();pop.document.write(doc);pop.document.close();pop.opener=null}catch(_){const blob=new Blob([doc],{type:"text/html"}),url=URL.createObjectURL(blob);pop.location.replace(url);setTimeout(()=>URL.revokeObjectURL(url),60000)}}
function button(label,title,heads,records){const b=document.createElement("button");b.type="button";b.textContent=label;b.addEventListener("click",()=>openCompare(title,heads,records));return b}
function convert(table,index){if(table.dataset.mcptResponsive===marker)return;table.dataset.mcptResponsive=marker;const{heads,records}=tableData(table),cols=heads.length,rows=records.length;if(!rows||cols<=4)return;const shell=document.createElement("div");shell.className="mcpt-compare-shell";const bar=document.createElement("div");bar.className="mcpt-compare-toolbar";bar.append(button("Compare all",document.title+" — comparison "+(index+1),heads,records));const count=document.createElement("span");count.className="mcpt-compare-count";count.textContent=rows+" records · "+cols+" fields";bar.append(count);shell.append(bar);if(rows<=3)shell.append(matrix(heads,records));else{const gi=groupIndex(heads,records),list=document.createElement("div");list.className="mcpt-group-list";if(gi>=0){const groups=new Map();records.forEach(r=>{const k=r[gi].text;if(!groups.has(k))groups.set(k,[]);groups.get(k).push(r)});groups.forEach((rs,key)=>{const d=document.createElement("details");d.className="mcpt-record-group";const s=document.createElement("summary");s.textContent=heads[gi]+": "+key;const body=document.createElement("div");body.className="mcpt-group-body";body.append(button("Compare group",document.title+" — "+key,heads,rs));body.append(rs.length<=3?matrix(heads,rs,new Set([gi])):cards(rs));d.append(s,body);list.append(d)})}else list.append(cards(records));shell.append(list)}table.classList.add("mcpt-wide-source");const wrap=table.closest(".table-wrap,.table-scroll,.table-shell")||table;wrap.insertAdjacentElement("afterend",shell)}
function init(){if(document.documentElement.dataset.mcptReportShell===marker)return;document.documentElement.dataset.mcptReportShell=marker;classifyGrids();buildSidebar();qa("table").forEach(convert)}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();
'''

_STYLE_RE = re.compile(r"<style>\s*/\*\s*MCPT_REPORT_(?:MONOCHROME_THEME_V1|SHELL_V2|SHELL_V3|SHELL_V4)\s*\*/.*?</style>\s*", re.I|re.S)
_SCRIPT_RE = re.compile(r"<script>\s*/\*\s*MCPT_REPORT_SHELL_V[234]\s*\*/.*?</script>\s*", re.I|re.S)
_META_RE = re.compile(r'<meta\s+name=["\']mcpt-dashboard-href["\'][^>]*>\s*', re.I)

def theme_report_document(document: str, *, dashboard_href: str = "../research_dashboard/index.html") -> str:
    cleaned = _STYLE_RE.sub("", document)
    cleaned = _SCRIPT_RE.sub("", cleaned)
    cleaned = _META_RE.sub("", cleaned)
    head = f'<meta name="mcpt-dashboard-href" content="{dashboard_href}">\n<style>{REPORT_SHELL_CSS}</style>\n'
    script = f'<script>{REPORT_SHELL_JS}</script>\n'
    cleaned = cleaned.replace("</head>", head + "</head>", 1) if "</head>" in cleaned else head + cleaned
    return cleaned.replace("</body>", script + "</body>", 1) if "</body>" in cleaned else cleaned + script

def discover_report_files(project_dir: Path) -> tuple[Path, ...]:
    reports = project_dir / "reports"
    if not reports.exists():
        return ()
    found = []
    for path in sorted(reports.rglob("report.html")):
        rel = path.relative_to(reports)
        if rel.parts and rel.parts[0] == "research_dashboard":
            continue
        found.append(path)
    return tuple(found)

def dashboard_href_for(project_dir: Path, report_path: Path) -> str:
    target = project_dir / "reports" / "research_dashboard" / "index.html"
    return Path(os.path.relpath(target, report_path.parent)).as_posix()

def theme_report_files(project_dir: Path, *, write: bool) -> tuple[Path, ...]:
    changed = []
    for path in discover_report_files(project_dir):
        before = path.read_text(encoding="utf-8")
        after = theme_report_document(before, dashboard_href=dashboard_href_for(project_dir, path))
        if before == after:
            continue
        changed.append(path)
        if write:
            path.write_text(after, encoding="utf-8", newline="\n")
    return tuple(changed)

def main() -> None:
    parser = argparse.ArgumentParser(description="Apply report shell v4 without rerunning research.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    project = Path(__file__).resolve().parent
    changed = theme_report_files(project, write=args.apply)
    print("\nRESEARCH REPORT SHELL V4\n========================")
    print(f"Reports found:              {len(discover_report_files(project))}")
    print(f"Reports needing update:     {len(changed)}")
    print("Bronze metric labels:       Enabled")
    print("Compact summary cards:      Enabled")
    print("Hierarchical menu:          Enabled")
    print("Scroll-follow highlight:    Enabled")
    print("Menu plus/minus markers:    Removed")
    print("Three-record comparison:    Full matrix")
    print("Compare-all new tab:        Enabled")
    print("Chart images modified:      0")
    print("Research calculations:      0")
    print("Market-data requests:       0")
    print("Preflight only. No report file was written." if args.preflight else "Existing report HTML updated from report shell v4.")

if __name__ == "__main__":
    main()
