(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  const versionsLink = document.createElement('a'); versionsLink.href = '/admin/versions'; versionsLink.textContent = '← All portfolio versions'; versionsLink.style.marginRight = '1rem'; document.querySelector('header > div').prepend(versionsLink);
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const slug = new URLSearchParams(location.search).get('slug') || 'fintech';
  let record, draft, projects, csrf, busy = false;
  const message = text => {$('#message').textContent = text;};
  async function api(path, data) {
    const response = await fetch(path, data === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify(data)});
    if (response.status === 401) {location.href='/admin/login'; throw Error('Sign in again.');}
    const value = await response.json();
    if (!response.ok) throw Error(value.error || 'The request failed. Your unsaved edits are still here.');
    return value;
  }
  function dirty() {return JSON.stringify(draft) !== JSON.stringify(record.draft);}
  function read() {for (const key of ['internal_name','headline','intro']) draft[key]=$('#'+key).value;}
  function render() {
    $('#count').textContent = draft.project_ids.length + ' / 3';
    $('#state').textContent = dirty() ? 'Unsaved edits · Published page unchanged' : record.has_changes ? 'Saved draft · Unpublished changes' : 'Saved draft matches the locally published page';
    $('#save').disabled = busy || !dirty();
    $('#publish').disabled = busy || dirty() || !record.has_changes;
    $('#selected').innerHTML=draft.project_ids.map((id,i)=>{const p=projects.find(p=>p.number===id);return `<div class="project-row"><img src="/${escape(p.image.replace('./',''))}" alt=""><span class="title">${escape(p.title)}</span><button type="button" data-up="${i}" aria-label="Move project ${id} up" ${i===0?'disabled':''}>↑</button><button type="button" data-down="${i}" aria-label="Move project ${id} down" ${i===draft.project_ids.length-1?'disabled':''}>↓</button><button type="button" data-remove="${id}" aria-label="Remove project ${id}">×</button></div>`;}).join('');
    $('#catalog').innerHTML=projects.map(p=>`<div class="project-row"><span class="title">${p.number} · ${escape(p.title)}</span><button type="button" data-add="${p.number}" ${draft.project_ids.includes(p.number)||draft.project_ids.length===3?'disabled':''}>${draft.project_ids.includes(p.number)?'Selected':'Add'}</button></div>`).join('');
    $('#mini').innerHTML=`<div class="mini-inner"><span>Fernando.</span><h3>${escape(draft.headline)}</h3><p>${escape(draft.intro)}</p></div><div class="projects">${draft.project_ids.map(id=>{const p=projects.find(p=>p.number===id);return `<div><img src="/${escape(p.image.replace('./',''))}" alt=""><h4>${escape(p.title)}</h4></div>`;}).join('')}</div>`;
  }
  $('#form').addEventListener('input',()=>{read();render();});
  $('#form').addEventListener('click',event=>{
    const b=event.target.closest('button');if(!b)return;
    if(b.dataset.add && draft.project_ids.length<3 && !draft.project_ids.includes(b.dataset.add)) draft.project_ids.push(b.dataset.add);
    if(b.dataset.remove) draft.project_ids=draft.project_ids.filter(id=>id!==b.dataset.remove);
    if(b.dataset.up!==undefined||b.dataset.down!==undefined){const i=Number(b.dataset.up??b.dataset.down),j=i+(b.dataset.up!==undefined?-1:1);if(j>=0&&j<draft.project_ids.length)[draft.project_ids[i],draft.project_ids[j]]=[draft.project_ids[j],draft.project_ids[i]];}
    render();
  });
  $('#form').addEventListener('submit',async event=>{
    event.preventDefault();if(busy)return;read();if(!draft.project_ids.length){message('Select at least one project.');return;}busy=true;render();
    try {record=await api('/api/versions/'+slug+'/save',{draft,revision:record.revision});draft=structuredClone(record.draft);message('Draft saved. The locally published page has not changed.');}
    catch(error){message(error.message);}finally{busy=false;render();}
  });
  $('#publish').addEventListener('click',async()=>{
    if(busy||dirty()||!record.has_changes)return;
    busy=true;render();
    try {record=await api('/api/versions/'+slug+'/publish',{revision:record.revision});message('Published locally. The same link now shows the saved content; no deployment occurred.');}
    catch(error){message(error.message);}finally{busy=false;render();}
  });
  $('#logout').addEventListener('click',async()=>{try{await api('/api/logout',{});location.href='/admin/login';}catch(error){message(error.message);}});
  window.addEventListener('beforeunload',event=>{if(record&&dirty()){event.preventDefault();event.returnValue='';}});
  (async()=>{try{const user=await api('/api/me');csrf=user.csrf;$('#account').textContent='Signed in as '+user.login;const data=await api('/api/versions');record=data.versions.find(v=>v.slug===slug);if(!record)throw Error('This version is unavailable.');projects=data.projects;draft=structuredClone(record.draft);for(const key of ['internal_name','slug','headline','intro'])$('#'+key).value=draft[key];$('#preview').href='/admin/preview/'+slug;$('#form').hidden=false;render();}catch(error){message(error.message);}})();
})();
