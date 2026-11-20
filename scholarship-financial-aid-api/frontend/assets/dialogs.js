import {el, icon, money, date, status} from './ui.js';

const dialog = document.querySelector('#record-dialog');
let revision = 0;
const close = () => dialog.close();

function open(title) {
  const heading = el('h2', {id: 'dialog-title'}, title);
  const body = el('div', {class: 'dialog-body'});
  const closeButton = el('button', {class: 'close quiet', 'aria-label': 'Close', onclick: close}, icon('close'));
  dialog.replaceChildren(el('div', {class: 'dialog-head'}, heading, closeButton), body);
  if (!dialog.open) dialog.showModal();
  const id = ++revision;
  return {body, current: () => dialog.open && revision === id};
}

function actions(label) {
  return el('div', {class: 'dialog-actions'},
    el('button', {type: 'button', class: 'secondary', onclick: close}, 'Cancel'),
    el('button', {type: 'submit', class: 'primary'}, label));
}

function properties(entries) {
  const list = el('dl', {class: 'properties'});
  for (const [label, value] of entries) list.append(el('dt', {}, label), el('dd', {}, value ?? '—'));
  return list;
}

export function openKeyDialog(key, onSave) {
  const {body} = open('API key');
  const input = el('input', {type: 'password', required: '', value: key, autocomplete: 'off'});
  const form = el('form', {},
    el('p', {class: 'help'}, 'The local demo key is school-demo-key. If your server uses a custom key, enter it here for this tab.'),
    el('div', {class: 'fields'}, el('label', {}, 'Request key', input)), actions('Save key'));
  form.addEventListener('submit', event => {
    event.preventDefault();
    close();
    onSave(input.value);
  });
  body.append(form);
}

export async function openApplicationForm(api, onCreated) {
  const {body, current} = open('New application');
  body.textContent = 'Loading form…';
  const fields = [
    ['Student', 'Student_ID', 'students', row => row.Student_Name],
    ['Scholarship (optional)', 'Scholarship_ID', 'scholarships', row => row.Scholarship_Name],
    ['Financial aid', 'Aid_ID', 'financial-aids', row => row.Aid_Description],
    ['Academic term', 'Term_ID', 'terms', row => row.Term_Name + ', ' + row.Academic_Year],
    ['Evaluator', 'Evaluator_ID', 'evaluators', row => row.Evaluator_Name],
  ];
  try {
    const data = await Promise.all(fields.map(field => api('/api/' + field[2])));
    if (!current()) return;
    const inputs = el('div', {class: 'fields'});
    fields.forEach(([label, key, , display], index) => {
      const select = el('select', {name: key});
      select.required = key !== 'Scholarship_ID';
      select.append(el('option', {value: ''}, select.required ? 'Choose…' : 'Financial aid only'));
      for (const row of data[index].data) select.append(el('option', {value: row[key]}, display(row)));
      inputs.append(el('label', {}, label, select));
    });
    const error = el('p', {role: 'alert', class: 'problem', hidden: ''});
    const form = el('form', {}, inputs, error, actions('Submit application'));
    form.addEventListener('submit', async event => {
      event.preventDefault();
      const submit = form.querySelector('button[type="submit"]');
      if (submit.disabled) return;
      const payload = Object.fromEntries(new FormData(form));
      if (!payload.Scholarship_ID) delete payload.Scholarship_ID;
      submit.disabled = true;
      error.hidden = true;
      try {
        const result = await api('/api/applications', {method: 'POST', body: JSON.stringify(payload)});
        if (current()) close();
        onCreated(result.data.Application_ID);
      } catch (failure) {
        error.textContent = failure.message;
        error.hidden = false;
      } finally {
        submit.disabled = false;
      }
    });
    body.replaceChildren(form);
    form.elements.Student_ID.focus();
  } catch (failure) {
    if (current()) body.textContent = failure.message;
  }
}

export async function openApplicationDetail(id, api) {
  const {body, current} = open('Application ' + id);
  body.textContent = 'Loading record…';
  try {
    const {data} = await api('/api/applications/' + encodeURIComponent(id));
    if (!current()) return;
    body.replaceChildren(properties([
      ['Student', data.Student.Student_Name], ['Status', status(data.Status)],
      ['Scholarship', data.Scholarship?.Scholarship_Name], ['Financial aid', data.Financial_Aid.Aid_Description],
      ['Academic term', data.Term.Term_Name + ', ' + data.Term.Academic_Year],
      ['Evaluator', data.Evaluator.Evaluator_Name], ['Filed', date(data.Application_Date)],
      ['Award', money(data.Award_Amount)], ['Disbursed', money(data.Disbursement_Summary.total_amount)],
      ['Requirements', data.Requirement_Summary.Verified + ' of ' + data.Requirement_Summary.total + ' verified'],
    ]));
  } catch (failure) {
    if (current()) body.textContent = failure.message;
  }
}

export function openScholarship(row) {
  open(row.Scholarship_Name).body.append(properties([
    ['Program ID', row.Scholarship_ID], ['Type', row.Scholarship_Type],
    ['Slots', row.Scholarship_Slots], ['Maximum GPA', row.Max_GPA_Allowed],
    ['Income limit', money(row.Max_Household_Income)],
  ]));
}
