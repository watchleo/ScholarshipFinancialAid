import {el, icon, money, date, status} from './ui.js';
import {openApplicationDetail, openApplicationForm, openKeyDialog, openScholarship} from './dialogs.js';

const pages = {
  overview: ['Overview', 'Scholarship & financial aid', 'An overview of student funding, applications and awards.', 'book'],
  applications: ['Applications', 'Applications', 'Find an application, check its status or submit a new one.', 'file'],
  students: ['Students', 'Students', 'Student records and academic information.', 'people'],
  scholarships: ['Scholarships', 'Scholarships', 'Program requirements, available slots and income limits.', 'cap'],
};
const view = document.querySelector('#view');
const notice = document.querySelector('#notice');
let key = sessionStorage.getItem('scholarship-key') ?? 'school-demo-key';
let page;
let loadNumber = 0;

async function api(path, options = {}) {
  const headers = {Accept: 'application/json', 'X-API-Key': key};
  if (options.body) headers['Content-Type'] = 'application/json';
  const response = await fetch(path, {...options, headers});
  if (response.status === 401) throw new Error('Access denied. Set your API key and try again.');
  if (!response.ok) {
    const json = await response.json().catch(() => ({}));
    const fields = json.error?.details?.fields;
    const details = fields ? Object.entries(fields).map(([k, v]) => k + ' ' + v).join('. ') : '';
    throw new Error([json.error?.message || 'Request failed (' + response.status + ').', details].filter(Boolean).join(' '));
  }
  return response.json();
}

function table(columns, rows, emptyMessage) {
  const head = el('tr');
  columns.forEach(name => head.append(el('th', {scope: 'col'}, name)));
  const body = el('tbody');
  for (const cells of rows) body.append(el('tr', {}, ...cells.map(value => el('td', {}, value ?? '—'))));
  if (!rows.length) {
    body.append(el('tr', {}, el('td', {colspan: columns.length, class: 'empty'}, emptyMessage)));
  }
  return el('div', {class: 'table-wrap'}, el('table', {}, el('thead', {}, head), body));
}

function recordButton(label, onClick, detail) {
  return el('div', {}, el('button', {class: 'record', onclick: onClick}, label),
    el('div', {class: 'record-detail'}, detail));
}

function applicationTable(items) {
  return table(['Student', 'Program / aid', 'Status', 'Filed', 'Award'], items.map(row => [
    recordButton(row.Student_Name, () => openApplicationDetail(row.Application_ID, api), row.Application_ID),
    row.Scholarship_Name || row.Aid_Type, status(row.Status), date(row.Application_Date), money(row.Award_Amount),
  ]), 'No applications found.');
}

function newApplication() {
  openApplicationForm(api, id => {
    if (page !== 'applications') location.hash = 'applications';
    else loadPage();
    notice.textContent = 'Application ' + id + ' submitted for review.';
    notice.hidden = false;
  });
}

function newButton() {
  return el('button', {class: 'primary', onclick: newApplication}, icon('plus', 14), 'New application');
}

function overview(summary, applications, scholarships) {
  const metrics = el('dl', {class: 'metrics'});
  for (const [label, value] of [
    ['Applications', applications.length], ['Pending review', summary.pending],
    ['Approved', summary.approved], ['Total awarded', money(summary.total_awarded)],
  ]) {
    metrics.append(el('div', {class: 'metric'}, el('dt', {}, label), el('dd', {}, value)));
  }
  const section = el('section', {class: 'program-section'}, el('h2', {}, 'Scholarship programs'));
  for (const row of scholarships.slice(0, 3)) {
    section.append(el('button', {class: 'program-link', onclick: () => openScholarship(row)},
      icon('cap', 19), row.Scholarship_Name, el('span', {class: 'sub'}, row.Scholarship_Slots + ' slots'), icon('chevron', 14)));
  }
  if (!scholarships.length) section.append(el('p', {class: 'empty'}, 'No scholarship programs yet.'));
  if (scholarships.length > 3) section.append(el('a', {href: '#scholarships', class: 'more'}, 'All scholarships', icon('arrow', 14)));
  return el('div', {}, metrics,
    el('section', {}, el('div', {class: 'section-head'}, el('h2', {}, 'Recent applications'), newButton()),
      applicationTable(applications.slice(-4).reverse()),
      el('a', {href: '#applications', class: 'more'}, 'All applications', icon('arrow', 14))),
    section);
}

function directory(items, currentPage) {
  const isApplications = currentPage === 'applications';
  const search = el('input', {type: 'search', placeholder: 'Search ' + currentPage + '…', 'aria-label': 'Search ' + currentPage});
  const toolbar = el('div', {class: 'toolbar'}, search);
  const result = el('div');
  const filter = el('select', {'aria-label': 'Filter by status'});
  if (isApplications) {
    filter.append(el('option', {value: ''}, 'All statuses'));
    for (const name of ['Pending', 'Approved', 'Rejected']) filter.append(el('option', {}, name));
    toolbar.append(filter, newButton());
  }
  const fields = isApplications
    ? ['Student_Name', 'Application_ID', 'Status', 'Scholarship_Name', 'Aid_Type']
    : ['Student_Name', 'Student_ID', 'Program', 'Email'];
  function showMatches() {
    const query = search.value.trim().toLowerCase();
    const rows = items.filter(row =>
      (!filter.value || row.Status === filter.value) &&
      fields.some(field => String(row[field] ?? '').toLowerCase().includes(query)));
    if (isApplications) result.replaceChildren(applicationTable(rows));
    else result.replaceChildren(table(['Student', 'Program', 'Year', 'GPA', 'Household income', 'Email'],
      rows.map(row => [
        el('div', {}, row.Student_Name, el('div', {class: 'record-detail'}, row.Student_ID)),
        row.Program, row.Year_Level, row.GPA, money(row.Household_Income), row.Email,
      ]), 'No students found.'));
  }
  search.addEventListener('input', showMatches);
  filter.addEventListener('change', showMatches);
  showMatches();
  return el('div', {}, toolbar, result);
}

function scholarshipsTable(items) {
  return table(['Program', 'Type', 'Slots', 'Maximum GPA', 'Income limit'], items.map(row => [
    recordButton(row.Scholarship_Name, () => openScholarship(row), row.Scholarship_ID),
    row.Scholarship_Type, row.Scholarship_Slots, row.Max_GPA_Allowed, money(row.Max_Household_Income),
  ]), 'No scholarship programs found.');
}

async function loadPage() {
  const revision = ++loadNumber;
  const hash = location.hash.slice(1);
  page = Object.hasOwn(pages, hash) ? hash : 'overview';
  const [label, heading, description, symbol] = pages[page];
  document.title = label + ' · Financial aid office';
  document.querySelector('#title').textContent = heading;
  document.querySelector('#crumb').textContent = label;
  document.querySelector('#description').textContent = description;
  document.querySelector('#page-icon').replaceChildren(icon(symbol, 38));
  document.querySelectorAll('nav a').forEach(link => {
    if (link.dataset.page === page) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
  view.setAttribute('aria-busy', 'true');
  view.textContent = 'Loading records…';
  try {
    let content;
    if (page === 'overview') {
      const [summary, apps, programs] = await Promise.all([
        api('/api/reports/summary'), api('/api/applications'), api('/api/scholarships'),
      ]);
      content = overview(summary, apps.data, programs.data);
    } else {
      const requestedPage = page;
      const {data} = await api('/api/' + requestedPage);
      content = requestedPage === 'scholarships' ? scholarshipsTable(data) :
        directory(requestedPage === 'applications' ? data.slice().reverse() : data, requestedPage);
    }
    if (revision === loadNumber) view.replaceChildren(content);
  } catch (failure) {
    if (revision === loadNumber) view.replaceChildren(el('div', {class: 'problem', role: 'alert'}, failure.message,
      el('button', {class: 'retry', onclick: loadPage}, 'Retry')));
  } finally {
    if (revision === loadNumber) view.setAttribute('aria-busy', 'false');
  }
}

document.querySelector('.skip').addEventListener('click', event => {
  event.preventDefault();
  document.querySelector('#content').focus();
});
document.querySelectorAll('[data-icon]').forEach(node => node.append(icon(node.dataset.icon)));
document.querySelector('#key-button').addEventListener('click', () => openKeyDialog(key, value => {
  key = value;
  sessionStorage.setItem('scholarship-key', key);
  notice.hidden = true;
  loadPage();
}));
document.querySelectorAll('nav a, .brand').forEach(link => {
  link.addEventListener('click', () => { notice.hidden = true; });
});
window.addEventListener('hashchange', loadPage);
loadPage();
