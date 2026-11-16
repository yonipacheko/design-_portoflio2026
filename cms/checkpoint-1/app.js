(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const escape = (v) => String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const catalog = window.portfolioProjects.filter(p => p.caseStudyUrl).map(p => ({...p,image:'../../dist/'+p.image.replace('./','')}));
  const samples = [
    {id:1,name:'Fintech opportunities',slug:'fintech',status:'Live',headline:'Making complex financial products feel simple.',intro:'I’m Fernando, a product designer connecting clarity, trust and useful interactions in financial services.',projects:['01','03','05']},
    {id:2,name:'Spatial & interaction design',slug:'spatial-design',status:'Draft',headline:'Making powerful tools easier to work with.',intro:'Exploring how contextual controls and spatial interactions can help people understand complex systems.',projects:['06','07']},
    {id:3,name:'Independent consultancy',slug:'consulting',status:'Live',headline:'Clear thinking. Practical product design.',intro:'Helping teams turn fragmented experiences into coherent products, from the first conversation to a working prototype.',projects:['05','01','07']},
    {id:4,name:'Earlier application',slug:'earlier-application',status:'Archived',headline:'Designing with purpose.',intro:'An earlier selection of financial product and interaction design work.',projects:['01','02']}
  ];
  let versions = structuredClone(samples), current = null, filter = 'All', sequence = 5;
  function project(id) { return catalog.find(p => p.number === id); }
  function toast(text) { $('#toast').textContent=text; $('#toast').style.display='block'; clearTimeout(toast.timer); toast.timer=setTimeout(()=>$('#toast').style.display='none',4000); }
  function miniature(v) {
    return `<div class="mini-inner"><div class="brand">Fernando<span>.</span></div><h3>${escape(v.headline)}</h3><p>${escape(v.intro)}</p></div><div class="projects">${v.projects.map(id=>{const p=project(id);return `<div><img src="${escape(p.image)}" alt="${escape(p.imageAlt)}"><h4>${escape(p.title)}</h4></div>`;}).join('')}</div>`;
  }
  function render() {
    const term=$('#search').value.trim().toLowerCase();
    const visible=versions.filter(v=>(filter==='All'||v.status===filter)&&`${v.name} ${v.headline}`.toLowerCase().includes(term));
    $('#cards').innerHTML=visible.map(v=>`<article class="card"><div class="thumbnail"><span class="sample-stamp">SAMPLE VERSION</span><div class="tiny-brand">Fernando.</div><h3>${escape(v.headline)}</h3><div class="thumbs">${v.projects.map(id=>`<img src="${escape(project(id).image)}" alt="">`).join('')}</div></div><div class="card-body"><div class="card-top"><h2>${escape(v.name)}</h2><span class="badge ${v.status}">${v.status}</span></div><p class="card-path">/for/${escape(v.slug)}</p><p class="card-projects">${v.projects.map(id=>`${id} · ${escape(project(id).category)}`).join('<br>')}</p><div class="card-actions"><button data-action="edit" data-id="${v.id}">Edit</button><button data-action="preview" data-id="${v.id}">Preview</button><button data-action="duplicate" data-id="${v.id}">Duplicate</button></div><p class="sample-note">Sample status · No live link or traffic data</p></div></article>`).join('') || '<p class="empty">No versions match this view.</p>';
  }
  function open(v) {
    current=structuredClone(v); $('#gallery').hidden=true; $('#editor').hidden=false;
    for(const key of ['name','slug','headline','intro']) $('#'+key).value=current[key];
    $('#editor-title').textContent=current.id?'Edit version':'New version'; update(); window.scrollTo(0,0);
  }
  function read() {for(const key of ['name','slug','headline','intro']) current[key]=$('#'+key).value;}
  function update() {
    read(); $('#path').textContent='/for/'+current.slug; $('#count').textContent=current.projects.length+' / 3'; $('#mini').innerHTML=miniature(current);
    $('#selected').innerHTML=current.projects.map((id,i)=>`<div class="project-row"><img src="${escape(project(id).image)}" alt=""><span class="title"><small>${id}</small><br>${escape(project(id).title)}</span><button type="button" data-move="${i}" data-direction="-1" aria-label="Move project ${id} up" ${i===0?'disabled':''}>↑</button><button type="button" data-move="${i}" data-direction="1" aria-label="Move project ${id} down" ${i===current.projects.length-1?'disabled':''}>↓</button><button type="button" data-remove="${id}" aria-label="Remove project ${id}">×</button></div>`).join('') || '<p class="muted">No projects selected yet.</p>';
    $('#catalog').innerHTML=catalog.map(p=>`<div class="project-row"><img src="${escape(p.image)}" alt=""><span class="title">${p.number} · ${escape(p.title)}</span><button type="button" data-add="${p.number}" ${current.projects.includes(p.number)||current.projects.length===3?'disabled':''}>${current.projects.includes(p.number)?'Selected':'Add'}</button></div>`).join('');
  }
  function preview(v) {$('#landing-body').innerHTML='<div class="mini">'+miniature(v)+'</div>'; $('#landing').showModal();}
  $('.tabs').addEventListener('click',e=>{if(!e.target.dataset.filter)return;filter=e.target.dataset.filter;document.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b===e.target)));render();});
  $('#search').addEventListener('input',render);
  $('#cards').addEventListener('click',e=>{const b=e.target.closest('[data-action]');if(!b)return;const v=versions.find(v=>v.id===Number(b.dataset.id));if(b.dataset.action==='edit')open(v);if(b.dataset.action==='preview')preview(v);if(b.dataset.action==='duplicate'){const copy=structuredClone(v);copy.id=sequence++;copy.name=v.name+' — copy';copy.slug=v.slug+'-copy-'+copy.id;copy.status='Draft';versions.unshift(copy);open(copy);toast('Duplicated as a sample draft with a new link name.');}});
  $('#new').addEventListener('click',()=>open({id:null,name:'',slug:'',status:'Draft',headline:'Making the complicated feel simple.',intro:'',projects:[]}));
  $('#back').addEventListener('click',()=>{if(current&&JSON.stringify(current)!==JSON.stringify(versions.find(v=>v.id===current.id))&&!confirm('Leave this editor? Unsaved sample edits will be discarded.'))return;$('#editor').hidden=true;$('#gallery').hidden=false;render();});
  $('#form').addEventListener('input',update);
  $('#form').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.add){if(current.projects.length<3&&!current.projects.includes(b.dataset.add))current.projects.push(b.dataset.add);update();}if(b.dataset.remove){current.projects=current.projects.filter(id=>id!==b.dataset.remove);update();}if(b.dataset.move){const i=Number(b.dataset.move),j=i+Number(b.dataset.direction);if(j>=0&&j<current.projects.length)[current.projects[i],current.projects[j]]=[current.projects[j],current.projects[i]];update();}});
  $('#form').addEventListener('submit',e=>{e.preventDefault();read();if(current.projects.length===0){toast('Choose at least one project.');return;}if(versions.some(v=>v.id!==current.id&&v.slug===current.slug)){toast('Choose a unique link name.');return;}const saved=structuredClone(current);saved.id=saved.id||sequence++;saved.status='Draft';const i=versions.findIndex(v=>v.id===saved.id);if(i>=0)versions[i]=saved;else versions.unshift(saved);current=structuredClone(saved);toast('Sample draft saved for this session only. Nothing published.');});
  $('#preview').addEventListener('click',()=>{read();preview(current);});$('#close').addEventListener('click',()=>$('#landing').close());
  render();
})();
