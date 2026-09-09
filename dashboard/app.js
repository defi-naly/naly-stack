'use strict';
const $ = selector => document.querySelector(selector);
const el = (tag, text, cls) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (cls) node.className = cls; return node; };
let state, selected, pending = false;
const statuses = [['backlog', 'Queued'], ['doing', 'In progress'], ['review', 'Review'], ['blocked', 'Blocked / handed off'], ['done', 'Done']];
const date = value => value ? new Date(value).toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}) : 'No recorded activity';
function renderBoard() {
  const query = $('#search').value.toLowerCase();
  const tasks = state.tasks.filter(t => [t.title,t.id,t.owner,t.assigned,t.skills,t.notes].join(' ').toLowerCase().includes(query));
  $('#board').replaceChildren();
  for (const [status, label] of statuses) {
    const column = el('div', undefined, `column ${status}`);
    const matching = tasks.filter(t => t.status === status);
    const heading = el('div', undefined, 'column-heading');
    heading.append(el('span', undefined, 'dot'), el('strong', label), el('span', matching.length));
    column.append(heading);
    for (const task of matching) {
      const card = el('button', undefined, 'task'); card.type = 'button';
      card.append(el('span', task.id, 'task-id'), el('h3', task.title || 'Untitled task'));
      card.append(el('div', task.status === 'review' ? `${task.owner || 'Unassigned'} → ${task.reviewer || 'Reviewer'}` : task.owner || task.assigned || 'Unassigned', 'task-meta'));
      if (task.role) card.append(el('span', task.role, 'tag'));
      card.addEventListener('click', () => openTask(task));
      column.append(card);
    }
    if (!matching.length) column.append(el('p', query ? 'No matching tasks' : status === 'backlog' ? 'Room for the next idea.' : 'Nothing here yet.', 'empty'));
    $('#board').append(column);
  }
}
function render() {
  $('#project').textContent = state.project;
  $('#agent-count').textContent = state.agents.length;
  $('#task-count').textContent = `${state.tasks.filter(t => t.status !== 'done').length} open · ${state.tasks.length} total`;
  $('#agents').replaceChildren();
  for (const agent of state.agents) {
    const card = el('article', undefined, 'agent');
    const content = el('div'); content.append(el('h3', agent.name), el('p', [agent.provider,agent.model,agent.role].filter(Boolean).join(' · ') || 'Board participant'));
    card.append(el('span', agent.name.slice(0,2).toUpperCase(), 'avatar'), content,
      el('p', `${agent.tasks.length ? agent.tasks.join(', ') : 'No open tasks'} · ${date(agent.last_event)}`, 'agent-work'));
    $('#agents').append(card);
  }
  if (!state.agents.length) $('#agents').append(el('p', 'Add agents to your sessions file or register a session with naly name.', 'empty'));
  renderBoard();
  $('#events').replaceChildren();
  for (const event of state.events.slice(0,12)) {
    const row = el('div', undefined, 'event');
    row.append(el('time', date(event.time)), el('strong', event.actor), el('p', `${event.verb} ${event.task === '-' ? '' : event.task}${event.target !== '-' && event.target !== '*' ? ` → ${event.target}` : ''}${event.message ? ` · ${event.message}` : ''}`));
    $('#events').append(row);
  }
  if (!state.events.length) $('#events').append(el('p', 'Activity will appear here as your team picks up work.', 'empty'));
}
async function refresh() {
  try {
    const response = await fetch('/api/state', {cache:'no-store'});
    const data = await response.json(); if (!response.ok) throw Error(data.error);
    const changed = JSON.stringify(state) !== JSON.stringify(data);
    state = data; if (changed) render();
    $('#connection').textContent = 'Live · just updated'; $('#connection').className = 'live';
    if (data.warnings.length) notify(data.warnings.join(' '));
  } catch (error) {
    $('#connection').textContent = 'Disconnected · retrying'; $('#connection').className = '';
    notify(`Updates paused: ${error.message}. The board shown may be out of date.`);
  }
}
function notify(message) { $('#notice').textContent = message; $('#notice').hidden = false; }
function field(form, name, label, options) {
  const wrap = el('label', label);
  const input = el(options ? 'select' : 'input'); input.name = name;
  if (options) for (const [value,text] of options) { const option = el('option',text); option.value = value; input.append(option); }
  else input.maxLength = 4000;
  wrap.append(input); form.append(wrap); return input;
}
function openTask(task) {
  selected = {...task}; $('#detail-id').textContent = task.id; $('#detail-title').textContent = task.title;
  const fields = el('dl');
  for (const [key,label] of [['status','Status'],['owner','Owner'],['assigned','Assigned'],['reviewer','Reviewer'],['branch','Branch'],['skills','Skills'],['notes','Notes'],['verdict','Verdict'],['updated','Updated']]) {
    if (task[key]) fields.append(el('dt',label),el('dd',task[key]));
  }
  $('#detail-fields').replaceChildren(fields); $('#task-controls').replaceChildren(); $('#task-actions').replaceChildren(); $('#task-form .form-error').textContent = '';
  if (task.status === 'review') {
    field($('#task-controls'),'reason','Feedback (required when returning work)');
    for (const [action,label] of [['pass','Pass review'],['fail','Return for changes']]) {
      const button = el('button',label,action === 'pass' ? 'primary' : ''); button.name = 'action'; button.value = action; button.type = 'submit'; $('#task-actions').append(button);
    }
  } else if (['backlog','blocked'].includes(task.status) && state.agents.length) {
    field($('#task-controls'),'target','Hand off to',state.agents.map(a=>[a.name,a.name]));
    field($('#task-controls'),'notes','Handoff notes').value = task.notes || '';
    const button = el('button','Hand off task','primary');button.name='action';button.value='handoff';button.type='submit';$('#task-actions').append(button);
  } else $('#task-controls').append(el('p', task.status === 'doing' ? 'This agent owns the work. Ask it to hand off from its session when ready.' : 'This task has no dashboard actions.', 'hint'));
  $('#task-dialog').showModal();
}
async function submit(form, data, dialog) {
  if (pending) return; pending = true;
  const buttons = [...form.querySelectorAll('button[type="submit"]')]; buttons.forEach(b=>b.disabled=true);
  form.querySelector('.form-error').textContent = '';
  try {
    const response = await fetch('/api/action', {method:'POST',headers:{'Content-Type':'application/json','X-Naly-Token':state.token},body:JSON.stringify(data)});
    const result = await response.json(); if (!response.ok) throw Error(result.error);
    dialog.close(); notify([result.message,result.warning].filter(Boolean).join(' · ')); await refresh();
  } catch (error) { form.querySelector('.form-error').textContent = error.message; }
  finally { pending = false; buttons.forEach(b=>b.disabled=false); }
}
$('#new-task').addEventListener('click',()=>{
  if (!state) return;
  $('#create-form').reset(); $('#create-form .form-error').textContent='';
  $('#role-options').replaceChildren();
  for (const [value,text] of [['','Anyone can claim'],...[...new Set(state.agents.map(a=>a.role).filter(Boolean))].map(r=>[r,r])]) {
    const option=el('option',text); option.value=value; $('#role-options').append(option);
  }
  $('#create-dialog').showModal();
});
$('#create-form').addEventListener('submit',event=>{event.preventDefault();submit(event.target,{...Object.fromEntries(new FormData(event.target)),action:'create'},$('#create-dialog'));});
$('#task-form').addEventListener('submit',event=>{event.preventDefault();if (!event.submitter) return;submit(event.target,{...Object.fromEntries(new FormData(event.target)),action:event.submitter.value,id:selected.id,version:selected.version},$('#task-dialog'));});
for (const button of document.querySelectorAll('[data-close]')) button.addEventListener('click',()=>button.closest('dialog').close());
$('#search').addEventListener('input',()=>{if(state) renderBoard();});
async function poll() { await refresh(); setTimeout(poll,2000); }
poll();
