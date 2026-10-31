'use strict';
const $ = (s,r=document)=>r.querySelector(s);
const $$ = (s,r=document)=>[...r.querySelectorAll(s)];
const esc = s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const paths={
 moon:'<path d="M20.8 13a9 9 0 0 1-9.8-9.8A9 9 0 1 0 20.8 13Z"/>',
 sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.4 1.4m11.2 11.2L19 19M5 19l1.4-1.4M17.6 6.4 19 5"/>',
 bridge:'<path d="M3 17h18M5 17V10a7 7 0 0 1 14 0v7M9 17v-7a3 3 0 0 1 6 0v7"/>',
 upload:'<path d="M12 16V3m-5 5 5-5 5 5M4 15v5a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5"/>',
 folder:'<path d="M3 6a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>',
 plug:'<path d="m8 3 1 5m7-5-1 5M6 8h12v3a6 6 0 0 1-12 0Zm6 9v5"/>',
 search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
 chevron:'<path d="m9 5 7 7-7 7"/>',
 check:'<path d="m5 12 4 4L19 6"/>',
 clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 wave:'<path d="M3 10v4m4-8v12m5-15v18m5-15v12m4-8v4"/>',
 lock:'<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V6a4 4 0 0 1 8 0v4m-4 5v2"/>',
 file:'<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9Zm0 0v6h6M8 13h8m-8 4h6"/>',
 play:'<path d="m9 5 10 7-10 7Z"/>',
 pause:'<path d="M8 5v14m8-14v14"/>',
 copy:'<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
 download:'<path d="M12 3v12m-5-5 5 5 5-5M4 16v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4"/>',
 trash:'<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7"/>',
 plus:'<path d="M12 4v16M4 12h16"/>',
 refresh:'<path d="M20 7v5h-5M4 17v-5h5M5 8a8 8 0 0 1 13-3l2 2M4 17l2 2a8 8 0 0 0 13-3"/>',
 eye:'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
 edit:'<path d="m16 3 5 5-12 12-6 1 1-6ZM13 6l5 5"/>',
 close:'<path d="m5 5 14 14M19 5 5 19"/>',
 spark:'<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"/>'
};
const icon=n=>`<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${paths[n]||paths.file}</svg>`;
const templateNames={meeting:'会议纪要',interview:'面试复盘',general:'内容梳理'};
const statusNames={queued:'等待处理',transcribing:'正在转写',analyzing:'正在分析',ready:'已完成',error:'需要重试',cancelled:'已取消'};
const active=r=>r&&['queued','transcribing','analyzing'].includes(r.status);
const clock=s=>{s=Math.max(0,Math.floor(Number(s)||0));return s>=3600?`${Math.floor(s/3600)}:${String(Math.floor(s%3600/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`:`${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;};
const duration=s=>s>=3600?`${Math.floor(s/3600)} 小时 ${Math.round(s%3600/60)} 分钟`:s>=60?`${Math.floor(s/60)} 分 ${Math.round(s%60)} 秒`:`${Math.round(s||0)} 秒`;
const bytes=n=>n>=1024**3?`${(n/1024**3).toFixed(1)} GB`:`${(n/1024**2).toFixed(1)} MB`;
const date=s=>new Intl.DateTimeFormat('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(s));
const S={view:'home',id:null,config:null,items:[],counts:{},template:'meeting',profile:'ark',detail:null,tab:'analysis',search:'',filter:'all',editing:false,transcriptQuery:'',profileDrafts:[],selectedProfile:'ark',version:null,uploading:false,busy:false};
let pollTimer=null,searchTimer=null,dragCount=0,audioId=null,uploadPercent=0,uploadName='';
const api=async(url,options={})=>{
 const r=await fetch(url,{...options,headers:options.body?{'Content-Type':'application/json',...options.headers}:options.headers});
 let data;try{data=await r.json();}catch{throw new Error('服务暂时无法响应，请重新打开听桥');}
 if(!r.ok)throw new Error(typeof data.detail==='string'?data.detail:'操作失败，请稍后重试');
 return data;
};
function toast(message,error=false){const node=document.createElement('div');node.className='toast'+(error?' error':'');node.textContent=message;$('#toasts').appendChild(node);setTimeout(()=>node.remove(),error?8000:4000);}
function go(view,id){location.hash=view==='detail'?`record/${id}`:view;}
function statusHTML(r){return `<span class="status ${esc(r.status)}"><i class="dot"></i>${statusNames[r.status]||'已保存'}</span>`;}
function profileOptions(selected){return S.config.profiles.map(p=>`<option value="${esc(p.id)}" ${p.id===selected?'selected':''}>${esc(p.name)} · ${esc(p.model)}</option>`).join('');}
function templateOptions(selected){return Object.entries(templateNames).map(([id,label])=>`<option value="${id}" ${id===selected?'selected':''}>${label}</option>`).join('');}
function sidebar(){
 $('#sidebar').innerHTML=`<div class="brand"><img src="/static/icon.svg" alt="听桥"><div><div class="brand-name">听桥</div><small>TINGQIAO</small></div></div>
 <div class="nav-label">你的声音工作台</div><nav class="nav" aria-label="主导航">
 <button class="nav-button ${S.view==='home'?'active':''}" data-nav="home" title="开始分析">${icon('upload')}<span>开始分析</span></button>
 <button class="nav-button ${['archive','detail'].includes(S.view)?'active':''}" data-nav="archive" title="录音档案">${icon('folder')}<span>录音档案</span><span class="count" id="archive-count">${S.counts.total||0}</span></button>
 <div class="sidebar-divider"></div><button class="nav-button ${S.view==='models'?'active':''}" data-nav="models" title="模型连接">${icon('plug')}<span>模型连接</span></button></nav>
 <div class="sidebar-bottom"><div class="ready-line"><i class="dot"></i>本地转写已就绪</div><p>录音留在本机<br>把重要的内容，清晰留下。</p></div><div class="sidebar-foot"><span>LOCAL FIRST</span><span>v1.0</span></div>`;
}
function themeButton(){const dark=window.TingqiaoTheme.current()==='dark',label=dark?'日间模式':'夜间模式';return `<button class="theme-toggle" data-action="toggle-theme" title="切换到${label}" aria-label="切换到${label}" aria-pressed="${dark}">${icon(dark?'sun':'moon')}<span>${label}</span></button>`;}
document.addEventListener('tingqiao-theme-change',()=>{$$('[data-action="toggle-theme"]').forEach(button=>button.outerHTML=themeButton());});
function topbar(label){const p=S.config.profiles.find(p=>p.id===S.profile)||S.config.profiles[0];return `<div class="topbar"><div class="breadcrumb">听桥 <span>/</span> <b>${label}</b></div><div class="top-actions"><button class="search-shortcut" data-action="search">${icon('search')}<span>搜索录音</span><kbd>Ctrl K</kbd></button>${themeButton()}<button class="model-chip" data-nav="models" title="更换分析模型"><i class="dot"></i>${esc(p.name)}</button></div></div>`;}
function recordRows(items){
 if(!items.length)return `<div class="empty-state">${icon('wave')}<strong>${S.search?'没有找到匹配的录音':'这里会留下你的每一次思考'}</strong><p>${S.search?'试试其他标题或内容关键词':'上传第一段录音，识别和分析结果会自动保存在这里。'}</p></div>`;
 return items.map(r=>`<article class="record-row" data-record="${r.id}" tabindex="0" role="button" aria-label="打开 ${esc(r.title)}"><div class="file-icon">${icon('wave')}<span>${esc(r.original_name.split('.').at(-1).toUpperCase().slice(0,5))}</span></div><div class="record-meta"><div class="record-title">${esc(r.title)}</div><div class="record-sub"><span>${date(r.created_at)}</span><span>·</span><span>${r.duration?duration(r.duration):bytes(r.size)}</span><span class="tag">${templateNames[r.template]||'录音分析'}</span></div></div><div class="record-state">${statusHTML(r)}<small>${esc(active(r)?r.message:r.analysis_model||'本地存档')}</small></div><span class="row-arrow">${icon('chevron')}</span></article>`).join('');
}
function home(){
 $('#main').innerHTML=topbar('开始分析')+`<section class="hero"><div><div class="eyebrow">声音有迹，思考有桥</div><h1>从一段录音，到一份清晰的记录。</h1><p>拖入录音，听桥会完成转写、分析和归档。</p></div><div class="hero-mark" aria-hidden="true">${'<i></i>'.repeat(7)}</div></section>
 <section class="upload-card"><div class="dropzone" id="dropzone"><div class="upload-icon">${icon('upload')}</div><h2>把录音拖到这里</h2><p class="formats">支持 M4A、MP3、WAV、FLAC 等格式 · 单个文件最大 1 GB</p><div class="upload-buttons"><button class="btn btn-primary" data-action="pick">${icon('plus')}选择录音</button><span>识别、分析，自动完成</span></div></div>
 <div class="upload-options"><div><span class="field-label">你想如何整理这段录音？</span><div class="segment" role="group" aria-label="分析类型">${Object.entries(templateNames).map(([id,name])=>`<button data-template="${id}" class="${S.template===id?'active':''}">${name}</button>`).join('')}</div></div><div><label class="field-label" for="home-profile">分析模型</label><select id="home-profile">${profileOptions(S.profile)}</select></div></div></section>
 <div class="privacy-note">${icon('lock')}录音在本机转写，分析时仅将文字发送至所选模型。</div><div id="upload-status"></div>
 <section class="stats"><div class="stat"><div class="stat-icon">${icon('folder')}</div><div><strong>${S.counts.total||0}</strong><span>段录音已存档</span></div></div><div class="stat"><div class="stat-icon">${icon('check')}</div><div><strong>${S.counts.ready||0}</strong><span>份分析已完成</span></div></div><div class="stat"><div class="stat-icon">${icon('clock')}</div><div><strong>${Math.round((S.counts.duration||0)/60)}</strong><span>分钟声音已留下</span></div></div></section>
 <div class="section-heading"><h2>最近记录</h2><button class="text-link" data-nav="archive">查看全部 ${icon('chevron')}</button></div><div class="record-list" id="home-records">${recordRows(S.items.slice(0,5))}</div><div class="page-footer">每一段声音，都值得被认真听见。</div>`;
 renderUploadStatus();
}
function archive(){
 $('#main').innerHTML=topbar('录音档案')+`<div class="page-title"><h1>录音档案</h1><p>声音、文字与分析，都在这里。</p></div><div class="archive-tools"><div class="search-input">${icon('search')}<input id="archive-search" type="search" placeholder="搜索标题、转写内容或分析…" value="${esc(S.search)}" autocomplete="off"></div><div class="segment">${[['all','全部录音'],['processing','处理中'],['ready','已完成'],['error','待重试']].map(([id,label])=>`<button data-filter="${id}" class="${S.filter===id?'active':''}">${label}</button>`).join('')}</div></div><div class="record-list" id="archive-records">${recordRows(S.items)}</div><div class="page-footer">录音档案保存在这台电脑 · 不会自动上传原始音频</div>`;
}
function inlineMD(text){
 let s=esc(text);
 s=s.replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
 s=s.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,'<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
 s=s.replace(/\[(\d{1,4}:\d{2}(?::\d{2})?)((?:\s*[-–—,，、]\s*\d{1,4}:\d{2}(?::\d{2})?)*)\]/g,(full,first)=>{const t=first.split(':').map(Number);const n=t.length===3?t[0]*3600+t[1]*60+t[2]:t[0]*60+t[1];return `<button class="stamp-link" data-seek="${n}" title="回听 ${first}">${full}</button>`;});
 return s;
}
function markdown(text){
 const lines=String(text||'').split('\n');let html='',list='',code=false;
 const close=()=>{if(list){html+=`</${list}>`;list='';}};
 for(let i=0;i<lines.length;i++){
  const l=lines[i];
  if(/^```/.test(l)){close();html+=code?'</code></pre>':'<pre><code>';code=!code;continue;}
  if(code){html+=esc(l)+'\n';continue;}
  if(l.includes('|')&&i+1<lines.length&&/^\s*\|?\s*:?-{3}/.test(lines[i+1])){
   close();const cells=x=>x.trim().replace(/^\||\|$/g,'').split('|').map(x=>inlineMD(x.trim()));
   html+='<table><thead><tr>'+cells(l).map(x=>`<th>${x}</th>`).join('')+'</tr></thead><tbody>';i++;
   while(i+1<lines.length&&lines[i+1].includes('|')){i++;html+='<tr>'+cells(lines[i]).map(x=>`<td>${x}</td>`).join('')+'</tr>';}
   html+='</tbody></table>';continue;
  }
  let m;
  if(m=l.match(/^(#{1,4})\s+(.+)$/)){close();const n=Math.max(2,m[1].length);html+=`<h${n}>${inlineMD(m[2])}</h${n}>`;}
  else if(m=l.match(/^\s*([-*+]\s+|\d+[.)]\s+)(.*)$/)){
   const type=/^\d/.test(m[1])?'ol':'ul';if(list!==type){close();list=type;html+=`<${list}>`;}html+=`<li>${inlineMD(m[2])}</li>`;
  }else if(/^\s*---+\s*$/.test(l)){close();html+='<hr>';}
  else if(/^>\s?/.test(l)){close();html+=`<blockquote>${inlineMD(l.replace(/^>\s?/,''))}</blockquote>`;}
  else{close();if(l.trim())html+=`<p>${inlineMD(l)}</p>`;}
 }
 close();if(code)html+='</code></pre>';return html;
}
function progressHTML(r){return `<div class="progress-box"><div class="progress-top"><i class="spinner"></i><span>${esc(r.message||'正在处理')}</span></div><div class="progress-track"><div class="progress-fill ${r.status==='analyzing'?'indeterminate':''}" style="width:${Number(r.progress)||0}%"></div></div><small>${r.status==='queued'?'听桥会按上传顺序处理录音。':'可以离开这个页面，处理会在后台继续。'}</small></div>`;}
function analysisContent(r){
 let html='';
 if(active(r))html+=progressHTML(r);
 if(r.error)html+=`<div class="error-box"><strong>${r.transcription_complete?'转写已保存，分析可以重试':'录音处理遇到问题'}</strong><p>${esc(r.error)}</p></div>`;
 const content=S.version?.content||r.draft||r.analysis;
 if(content){if(r.draft&&active(r))html+='<div class="draft-label">分析正在生成</div>';html+=`<div class="reading">${markdown(content)}</div>`;}
 else if(!active(r)&&!r.error)html+=`<div class="empty-state">${icon('spark')}<strong>等待这段声音的下一步</strong><p>识别完成后，会在这里生成清晰的分析。</p></div>`;
 return html;
}
function transcriptContent(r){
 const q=S.transcriptQuery.trim().toLowerCase();
 const highlight=t=>{const s=esc(t);if(!q)return s;return s.replace(new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'),'gi'),x=>`<mark>${x}</mark>`);};
 const rows=r.transcript.map((s,i)=>({s,i})).filter(({s})=>!q||s.text.toLowerCase().includes(q));
 return `<div class="transcript-tools"><input id="transcript-search" placeholder="在转写中查找…" value="${esc(S.transcriptQuery)}" ${S.editing?'disabled':''}><button class="btn btn-secondary" data-action="${S.editing?'save-transcript':'edit-transcript'}" ${active(r)?'disabled':''}>${icon(S.editing?'check':'edit')}${S.editing?'保存校对':'校对文字'}</button>${S.editing?'<button class="btn btn-ghost" data-action="cancel-edit">取消</button>':''}</div><div id="transcript-rows">${rows.length?rows.map(({s,i})=>`<div class="transcript-row" data-start="${s.start}" data-end="${s.end}"><button class="time-button" data-seek="${s.start}">${icon('play')}${clock(s.start)}</button>${S.editing?`<textarea data-transcript-index="${i}" aria-label="${clock(s.start)} 转写文字">${esc(s.text)}</textarea>`:`<p>${highlight(s.text)}</p>`}</div>`).join(''):'<div class="transcript-empty">'+(q?'没有匹配的文字':'正在等待转写内容…')+'</div>'}</div>`;
}
function detail(){
 const r=S.detail;if(!r)return;
 const model=S.config.profiles.find(p=>p.id===r.profile_id);
 $('#main').innerHTML=topbar('录音档案')+`<div class="detail-header"><div class="detail-title-wrap"><input id="record-title" class="title-input" value="${esc(r.title)}" maxlength="160" aria-label="录音标题，修改后自动保存"><div class="detail-meta"><span>${date(r.created_at)}</span><span>·</span><span>${r.duration?duration(r.duration):'时长识别中'}</span><span>·</span><span>${bytes(r.size)}</span><span id="detail-status">${statusHTML(r)}</span></div></div><div class="detail-actions"><div class="export-wrap"><button class="btn btn-secondary" data-action="export">${icon('download')}导出</button><div class="export-links hidden" id="export-menu"><a href="/api/recordings/${r.id}/export?format=md" download>Markdown</a><a href="/api/recordings/${r.id}/export?format=txt" download>原文 TXT</a><a href="/api/recordings/${r.id}/export?format=json" download>JSON</a></div></div><button class="btn btn-ghost" data-action="delete" title="删除录音">${icon('trash')}</button></div></div>
 <div class="detail-grid"><section class="content-card"><div class="content-tabs"><button data-tab="analysis" class="${S.tab==='analysis'?'active':''}">分析结果</button><button data-tab="transcript" class="${S.tab==='transcript'?'active':''}">转写原文 <span id="segment-count">${r.transcript.length}</span></button></div>${S.tab==='analysis'?`<div class="content-toolbox"><select class="inline-version" id="version-select" aria-label="分析版本"><option value="">${r.versions.length?'最新分析':'分析结果'}</option>${r.versions.slice(1).map(v=>`<option value="${v.id}" ${S.version?.id===v.id?'selected':''}>${date(v.created_at)} · ${esc(v.model)}</option>`).join('')}</select><button class="btn btn-ghost" data-action="copy" ${!r.analysis&&!r.draft?'disabled':''}>${icon('copy')}复制</button></div>`:''}<div id="detail-content">${S.tab==='analysis'?analysisContent(r):transcriptContent(r)}</div></section>
 <aside class="detail-side"><section class="side-card"><h3>本次分析</h3><div class="form-field"><label for="detail-template">整理方式</label><select id="detail-template">${templateOptions(r.template)}</select></div><div class="form-field"><label for="detail-profile">分析模型</label><select id="detail-profile">${profileOptions(model?r.profile_id:S.config.default_profile)}</select></div><button class="btn btn-primary" data-action="${active(r)?'cancel':'reanalyze'}">${icon(active(r)?'close':'refresh')}${active(r)?'取消处理':r.analysis?'重新分析':'继续识别与分析'}</button><p class="side-note">已有转写会直接复用。重新分析成功后，上一版结果仍会保留。</p></section>
 <section class="side-card timing-card"><h3>处理记录</h3><div class="timing-lines"><span>本地转写</span><span>${r.timings.transcription?`${Math.round(r.timings.transcription)} 秒`:'—'}</span><span>模型分析</span><span>${r.timings.analysis?`${Math.round(r.timings.analysis)} 秒`:'—'}</span><span>转写片段</span><span>${r.transcript.length} 段</span></div></section><section class="side-card file-info-card"><h3>录音信息</h3><dl class="file-details"><dt>原始文件</dt><dd>${esc(r.original_name)}</dd><dt>分析模型</dt><dd>${esc(r.analysis_model||model?.model||'等待分析')}</dd><dt>存档位置</dt><dd>本机 / 听桥录音档案</dd></dl></section></aside></div>`;
 setupPlayer(r);
}
function models(){
 const p=S.profileDrafts.find(p=>p.id===S.selectedProfile)||S.profileDrafts[0];S.selectedProfile=p.id;
 $('#main').innerHTML=topbar('模型连接')+`<div class="page-title"><h1>连接你的思考模型</h1><p>选择习惯的模型，让每一份分析更合心意。</p></div><div class="settings-grid"><aside class="profiles">${S.profileDrafts.map(x=>`<button class="profile-item ${x.id===p.id?'active':''}" data-profile-edit="${esc(x.id)}">${icon('plug')}<div><strong>${esc(x.name||'新模型')}${S.config.default_profile===x.id?' · 默认':''}</strong><small>${esc(x.model||'等待配置')}</small></div></button>`).join('')}<button class="profile-add" data-action="add-profile">＋ 添加其他模型</button></aside><section class="settings-card"><h2>${esc(p.name||'新模型连接')}</h2><p class="intro">兼容 Chat Completions 接口，可连接云端模型或本地服务。</p><form id="model-form"><div class="form-grid"><div class="form-field"><label for="profile-name">连接名称</label><input class="input" id="profile-name" name="name" value="${esc(p.name)}" placeholder="例如：火山方舟" required></div><div class="form-field"><label for="profile-model">模型名称</label><input class="input" id="profile-model" name="model" value="${esc(p.model)}" placeholder="例如：ark-code-latest" list="model-suggestions" required><datalist id="model-suggestions">${['ark-code-latest','glm-latest','kimi-latest','deepseek-latest','minimax-latest','doubao-seed-2.1-pro','doubao-seed-2.1-lite','qwen3.5-4b-local'].map(n=>`<option value="${n}">`).join('')}</datalist></div><div class="form-field full"><label for="profile-url">接口地址 · Base URL</label><input class="input" id="profile-url" name="base_url" type="url" value="${esc(p.base_url)}" placeholder="https://…/v1" required><p class="form-help">填写接口基础地址即可，无需追加 /chat/completions。</p></div><div class="form-field full"><label for="profile-key">API 密钥</label><div class="secret-wrap"><input class="input" id="profile-key" name="api_key" type="password" autocomplete="new-password" value="${esc(p.api_key||'')}" placeholder="${p.has_key?'已加密保存，留空保持不变':'填写你的 API 密钥；本地服务可留空'}"><button type="button" data-action="toggle-key" aria-label="显示或隐藏本次输入的密钥">${icon('eye')}</button></div><p class="form-help">密钥使用系统安全存储（Windows DPAPI / macOS 钥匙串），不会写入页面代码或导出文件。</p></div><div class="form-field"><label for="profile-thinking">深度思考</label><select id="profile-thinking" name="thinking">${[['auto','由模型决定'],['enabled','开启深度思考'],['disabled','关闭深度思考']].map(([v,n])=>`<option value="${v}" ${p.thinking===v?'selected':''}>${n}</option>`).join('')}</select><p class="form-help">开启后通常需要更多时间，模型需支持 thinking 参数。</p></div><div class="form-field"><label for="profile-tokens">输出上限 · Tokens</label><input class="input" id="profile-tokens" name="max_tokens" type="number" min="512" max="32000" step="1" value="${p.max_tokens||6000}"><p class="form-help">长录音或思考模型可适当调高。</p></div></div><label class="model-default"><input type="checkbox" id="profile-default" ${S.config.default_profile===p.id?'checked':''}>设为新录音的默认分析模型</label><div class="settings-actions"><button type="button" class="btn btn-secondary" data-action="test-model">${icon('plug')}测试连接</button><button type="submit" class="btn btn-primary">${icon('check')}保存连接</button>${S.profileDrafts.length>1?'<button type="button" class="danger-link" data-action="remove-profile">移除此连接</button>':''}</div><div id="test-result"></div></form></section></div><div class="storage-note"><strong>关于你的数据</strong><br>原始录音、本地转写和分析档案保存在 应用目录下的 data 文件夹。<br>转写无需云端接口；生成分析时，转写文字会发送至当前选择的模型。</div>`;
}
function render(){sidebar();if(S.view==='home')home();else if(S.view==='archive')archive();else if(S.view==='detail')detail();else models();$('#player').classList.toggle('hidden',S.view!=='detail');if(S.view!=='detail')$('#audio').pause();}
function renderUploadStatus(){const el=$('#upload-status');if(el)el.innerHTML=S.uploading?`<div class="upload-progress">正在上传 ${esc(uploadName)} · ${uploadPercent}%<progress value="${uploadPercent}" max="100"></progress></div>`:'';}
function collectProfile(){const form=$('#model-form');if(!form)return;const p=S.profileDrafts.find(x=>x.id===S.selectedProfile);for(const n of ['name','model','base_url','thinking','max_tokens','api_key'])p[n]=form.elements[n].value;if($('#profile-default').checked)S.config.default_profile=p.id;}
async function saveProfiles(){collectProfile();S.config=await api('/api/config',{method:'POST',body:JSON.stringify({profiles:S.profileDrafts,default_profile:S.config.default_profile})});S.profileDrafts=structuredClone(S.config.profiles);S.profile=S.config.default_profile;toast('模型连接已保存');render();}
async function testModel(button){collectProfile();const p=S.profileDrafts.find(x=>x.id===S.selectedProfile);button.disabled=true;button.innerHTML='<i class="spinner"></i>正在测试';$('#test-result').innerHTML='';try{const result=await api('/api/models/test',{method:'POST',body:JSON.stringify(p)});$('#test-result').innerHTML=result.ok?`<div class="test-result">连接成功 · ${esc(result.model)} · ${result.seconds} 秒</div>`:`<div class="test-result error">${esc(result.error)}</div>`;}catch(e){$('#test-result').innerHTML=`<div class="test-result error">${esc(e.message)}</div>`;}finally{button.disabled=false;button.innerHTML=icon('plug')+'测试连接';}}
async function fetchList(){const params=new URLSearchParams();if(S.view==='archive'){if(S.search)params.set('q',S.search);if(S.filter!=='all')params.set('status',S.filter);}const result=await api('/api/recordings?'+params);S.items=result.items;S.counts=result.counts;const badge=$('#archive-count');if(badge)badge.textContent=S.counts.total||0;return result;}
async function route(){
 const hash=location.hash.replace(/^#\/?/,'');const match=hash.match(/^record\/([a-f0-9]{32})$/);
 const previous=S.view;S.view=match?'detail':['archive','models'].includes(hash)?hash:'home';S.id=match?match[1]:null;S.version=null;S.editing=false;
 if(S.view==='models'&&previous!=='models')S.profileDrafts=structuredClone(S.config.profiles);
 if(S.view==='detail'){
  try{const r=await api('/api/recordings/'+S.id);if(S.id!==r.id)return;S.detail=r;S.tab='analysis';S.transcriptQuery='';}catch(e){toast(e.message,true);go('archive');return;}
 }
 await fetchList();render();window.scrollTo(0,0);
}
async function tick(){
 try{
  const id=S.id,view=S.view;await fetchList();
  if(view!==S.view)return;
  if(view==='detail'&&id===S.id&&S.detail){
   const r=await api('/api/recordings/'+id);if(S.id!==id)return;const old=S.detail;S.detail=r;
   if(S.editing)return;
   if(old.status!==r.status||old.revision!==r.revision){detail();}
   else if(old.title!==r.title){const input=$('#record-title');if(input&&document.activeElement!==input)input.value=r.title;$('#player-name').textContent=r.title;}
   else if(active(r)){
    const content=$('#detail-content');if(content&&S.tab==='analysis')content.innerHTML=analysisContent(r);
    if(content&&S.tab==='transcript'&&old.transcript.length!==r.transcript.length)content.innerHTML=transcriptContent(r);
    const status=$('#detail-status');if(status)status.innerHTML=statusHTML(r);const count=$('#segment-count');if(count)count.textContent=r.transcript.length;
    setupPlayer(r);
   }
  }else if(view==='home'&&!S.uploading){home();}
  else if(view==='archive'){$('#archive-records').innerHTML=recordRows(S.items);}
 }catch(e){console.warn('刷新暂不可用');}
 finally{pollTimer=setTimeout(tick,S.counts.processing?1500:5000);}
}
function uploadFile(file){return new Promise((resolve,reject)=>{
 const form=new FormData();form.append('file',file);form.append('template',S.template);form.append('profile_id',S.profile);
 const xhr=new XMLHttpRequest();xhr.open('POST','/api/recordings');xhr.upload.onprogress=e=>{if(e.lengthComputable){uploadPercent=Math.round(e.loaded/e.total*100);renderUploadStatus();}};
 xhr.onload=()=>{let data;try{data=JSON.parse(xhr.responseText);}catch{reject(new Error('上传失败，请检查文件后重试'));return;}xhr.status>=200&&xhr.status<300?resolve(data):reject(new Error(data.detail||'上传失败'));};
 xhr.onerror=()=>reject(new Error('上传中断，请重试'));xhr.send(form);
});}
async function uploadFiles(files){
 if(S.uploading){toast('正在上传上一批录音，请稍等');return;}
 const p=S.config.profiles.find(p=>p.id===S.profile);
 if(!p?.has_key&&!/^http:\/\/(localhost|127\.0\.0\.1)(:|\/)/.test(p?.base_url||'')){toast('请先在模型连接中填写 API 密钥',true);go('models');return;}
 S.uploading=true;let last=null;
 for(const file of files){
  uploadName=file.name;uploadPercent=0;renderUploadStatus();
  if(file.size>1024**3){toast(file.name+' 超过1 GB，未上传',true);continue;}
  try{last=await uploadFile(file);toast(file.name+' 已加入处理队列');}catch(e){toast(e.message,true);}
 }
 S.uploading=false;renderUploadStatus();$('#file-picker').value='';await fetchList();
 if(last)go('detail',last.id);else render();
}
function setupPlayer(r){
 const audio=$('#audio');$('#player-name').textContent=r.title;
 if(r.duration&&audioId!==r.id){audioId=r.id;audio.src=r.media_url;$('#seek').value=0;audio.playbackRate=1;$('#speed').textContent='1×';}
 $('#play-toggle').disabled=!r.duration;updatePlayer();
}
function updatePlayer(){const a=$('#audio'),length=Number.isFinite(a.duration)?a.duration:S.detail?.duration||0;$('#player-time').textContent=`${clock(a.currentTime)} / ${clock(length)}`;if(!$('#seek').matches(':active'))$('#seek').value=length?a.currentTime/length*1000:0;$('#play-toggle').innerHTML=icon(a.paused?'play':'pause');$('#play-toggle').setAttribute('aria-label',a.paused?'播放录音':'暂停录音');$$('.transcript-row').forEach(n=>n.classList.toggle('playing',a.currentTime>=Number(n.dataset.start)&&a.currentTime<Number(n.dataset.end)));}
function seekTo(t){const a=$('#audio');if(!a.src){toast('录音还在准备，请稍等');return;}a.currentTime=Math.max(0,Number(t));a.play().catch(()=>toast('这段音频暂时无法播放',true));updatePlayer();}
function confirmDialog(title,message,action,label='确认'){const root=$('#modal-root');root.innerHTML=`<div class="modal-backdrop"><div class="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title"><h2 id="confirm-title">${esc(title)}</h2><p>${esc(message)}</p><div class="modal-actions"><button class="btn btn-secondary" id="modal-cancel">取消</button><button class="btn btn-danger" id="modal-confirm">${esc(label)}</button></div></div></div>`;$('#modal-cancel').onclick=()=>root.innerHTML='';$('#modal-confirm').onclick=async()=>{root.innerHTML='';try{await action();}catch(e){toast(e.message,true);}};$('#modal-cancel').focus();}
async function reanalyze(){const r=S.detail,profile=$('#detail-profile').value,template=$('#detail-template').value;await api(`/api/recordings/${r.id}/analyze`,{method:'POST',body:JSON.stringify({profile_id:profile,template})});S.detail=await api('/api/recordings/'+r.id);S.version=null;S.tab='analysis';detail();toast('已开始处理，已有转写会直接复用');}
async function saveTranscript(){const r=S.detail,segments=structuredClone(r.transcript);$$('textarea[data-transcript-index]').forEach(n=>segments[Number(n.dataset.transcriptIndex)].text=n.value);S.detail=await api('/api/recordings/'+r.id,{method:'PATCH',body:JSON.stringify({transcript:segments})});S.editing=false;detail();toast('校对已保存，可重新分析以更新结果');}
document.addEventListener('click',async e=>{
 const nav=e.target.closest('[data-nav]');if(nav){go(nav.dataset.nav);return;}
 const record=e.target.closest('[data-record]');if(record){go('detail',record.dataset.record);return;}
 const template=e.target.closest('[data-template]');if(template){S.template=template.dataset.template;home();return;}
 const filter=e.target.closest('[data-filter]');if(filter){S.filter=filter.dataset.filter;await fetchList();archive();return;}
 const tab=e.target.closest('[data-tab]');if(tab){if(S.editing){toast('请先保存或取消校对');return;}S.tab=tab.dataset.tab;detail();return;}
 const stamp=e.target.closest('[data-seek]');if(stamp){e.preventDefault();seekTo(stamp.dataset.seek);return;}
 const profile=e.target.closest('[data-profile-edit]');if(profile){collectProfile();S.selectedProfile=profile.dataset.profileEdit;models();return;}
 const button=e.target.closest('[data-action]');if(!button)return;
 try{
  switch(button.dataset.action){
   case 'toggle-theme':window.TingqiaoTheme.toggle();break;
   case 'pick':$('#file-picker').click();break;
   case 'search':S.search='';S.filter='all';if(S.view!=='archive'){go('archive');setTimeout(()=>$('#archive-search')?.focus(),150);}else $('#archive-search').focus();break;
   case 'export':$('#export-menu').classList.toggle('hidden');break;
   case 'copy':await navigator.clipboard.writeText(S.version?.content||S.detail.draft||S.detail.analysis);toast('分析内容已复制');break;
   case 'cancel':await api(`/api/recordings/${S.id}/cancel`,{method:'POST'});toast('已请求取消处理');break;
   case 'reanalyze':await reanalyze();break;
   case 'edit-transcript':S.editing=true;S.transcriptQuery='';detail();break;
   case 'cancel-edit':S.editing=false;detail();break;
   case 'save-transcript':await saveTranscript();break;
   case 'delete':confirmDialog('从档案中移除这段录音？','录音文件会移至本机听桥数据目录的 recycle 文件夹。',async()=>{await api('/api/recordings/'+S.id,{method:'DELETE'});go('archive');toast('录音已移除');},'移除录音');break;
   case 'toggle-key':$('#profile-key').type=$('#profile-key').type==='password'?'text':'password';break;
   case 'add-profile':collectProfile();const id=crypto.randomUUID().replaceAll('-','');S.profileDrafts.push({id,name:'新模型',base_url:'',model:'',thinking:'auto',max_tokens:6000,has_key:false});S.selectedProfile=id;models();$('#profile-name').focus();break;
   case 'remove-profile':if(S.profileDrafts.length<2)return;S.profileDrafts=S.profileDrafts.filter(p=>p.id!==S.selectedProfile);S.selectedProfile=S.profileDrafts[0].id;if(!S.profileDrafts.find(p=>p.id===S.config.default_profile))S.config.default_profile=S.selectedProfile;models();toast('点击保存连接后生效');break;
   case 'test-model':await testModel(button);break;
  }
 }catch(err){toast(err.message,true);}
});
document.addEventListener('submit',async e=>{if(e.target.id==='model-form'){e.preventDefault();try{await saveProfiles();}catch(err){toast(err.message,true);}}});
document.addEventListener('input',e=>{
 if(e.target.id==='archive-search'){S.search=e.target.value;clearTimeout(searchTimer);searchTimer=setTimeout(async()=>{await fetchList();if(S.view==='archive')$('#archive-records').innerHTML=recordRows(S.items);},250);}
 if(e.target.id==='transcript-search'){S.transcriptQuery=e.target.value;const selection=e.target.selectionStart;$('#detail-content').innerHTML=transcriptContent(S.detail);const input=$('#transcript-search');input.focus();input.setSelectionRange(selection,selection);}
});
document.addEventListener('change',async e=>{
 if(e.target.id==='home-profile')S.profile=e.target.value;
 if(e.target.id==='version-select'){try{S.version=e.target.value?await api(`/api/recordings/${S.id}/versions/${e.target.value}`):null;$('#detail-content').innerHTML=analysisContent(S.detail);}catch(err){toast(err.message,true);}}
});
document.addEventListener('focusout',async e=>{if(e.target.id==='record-title'&&S.detail&&e.target.value.trim()!==S.detail.title){try{S.detail=await api('/api/recordings/'+S.id,{method:'PATCH',body:JSON.stringify({title:e.target.value})});$('#player-name').textContent=S.detail.title;toast('标题已保存');}catch(err){toast(err.message,true);e.target.value=S.detail.title;}}});
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();const b=$('[data-action=search]');b?.click();}if(e.key==='Escape'){$('#modal-root').innerHTML='';$('#export-menu')?.classList.add('hidden');}if(e.key==='Enter'&&e.target.matches('[data-record]'))go('detail',e.target.dataset.record);if(e.key==='Enter'&&e.target.id==='record-title')e.target.blur();});
$('#file-picker').addEventListener('change',e=>uploadFiles([...e.target.files]));
window.addEventListener('dragenter',e=>{if([...e.dataTransfer.types].includes('Files')){e.preventDefault();dragCount++;$('#drag-overlay').classList.remove('hidden');}});
window.addEventListener('dragover',e=>{if([...e.dataTransfer.types].includes('Files')){e.preventDefault();e.dataTransfer.dropEffect='copy';}});
window.addEventListener('dragleave',e=>{e.preventDefault();dragCount=Math.max(0,dragCount-1);if(!dragCount)$('#drag-overlay').classList.add('hidden');});
window.addEventListener('drop',e=>{e.preventDefault();dragCount=0;$('#drag-overlay').classList.add('hidden');const files=[...e.dataTransfer.files];if(files.length)uploadFiles(files);});
$('#play-toggle').onclick=()=>{const a=$('#audio');a.paused?a.play().catch(()=>toast('录音暂时无法播放',true)):a.pause();};
$('#audio').addEventListener('timeupdate',updatePlayer);$('#audio').addEventListener('loadedmetadata',updatePlayer);$('#audio').addEventListener('play',updatePlayer);$('#audio').addEventListener('pause',updatePlayer);
$('#seek').addEventListener('input',e=>{const a=$('#audio');if(Number.isFinite(a.duration))a.currentTime=e.target.value/1000*a.duration;});
$('#speed').onclick=()=>{const a=$('#audio'),rates=[1,1.25,1.5,1.75,2,.75];a.playbackRate=rates[(rates.indexOf(a.playbackRate)+1)%rates.length];$('#speed').textContent=a.playbackRate+'×';};
window.addEventListener('hashchange',()=>route().catch(e=>toast(e.message,true)));
(async()=>{try{S.config=await api('/api/config');S.profile=S.config.default_profile;S.selectedProfile=S.profile;S.profileDrafts=structuredClone(S.config.profiles);await route();tick();}catch(e){$('#main').innerHTML=`<div class="empty-state"><strong>听桥暂时无法打开</strong><p>${esc(e.message)}</p><button class="btn btn-primary" id="reload-app">重新连接</button></div>`;$('#reload-app').onclick=()=>location.reload();}})();
