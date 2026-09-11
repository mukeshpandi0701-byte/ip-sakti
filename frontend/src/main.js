import './style.css';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

document.querySelector('#app').innerHTML = `
  <div class="shell">
    <header>
      <p class="eyebrow">SIH 2026 MVP</p>
      <h1>IP-SAKTI</h1>
      <p class="intro">An IP and regulatory navigator for Ayurveda and traditional knowledge.</p>
    </header>
    <section class="card">
      <form id="query-form">
        <label for="question">Ask an IP or regulatory question</label>
        <textarea id="question" name="question" rows="4" required maxlength="2000"
          placeholder="For example: How can I protect a traditional formulation brand?"></textarea>
        <div class="control-grid">
          <div>
            <label for="response-language">Response language preference</label>
            <select id="response-language" name="response_language">
              <option value="en">English</option>
              <option value="ta">தமிழ் (Tamil)</option>
              <option value="hi">हिन्दी (Hindi)</option>
            </select>
          </div>
          <div>
            <label for="jurisdiction">Context jurisdiction</label>
            <select id="jurisdiction" name="jurisdiction">
              <option value="india">🇮🇳 India</option>
              <option value="international">International</option>
            </select>
          </div>
        </div>
        <p class="preference-note">Language and jurisdiction are saved as request preferences only. No translation or jurisdiction analysis is performed yet.</p>
        <label for="files">Supporting files (optional)</label>
        <input id="files" name="files" type="file" multiple accept=".pdf,.txt,.docx,.jpg,.jpeg,.png,.webp" />
        <p id="selected-files" class="selected-files">No files selected.</p>
        <button type="submit">Ask IP-SAKTI</button>
      </form>
      <p id="status" class="status" role="status"></p>
    </section>
    <section id="result" class="result" hidden>
      <div class="response-label">IP-SAKTI RESPONSE</div>
      <p id="question-display" class="question-display"></p>
      <p id="classification" class="classification"></p>
      <p id="grounded" class="grounded"></p>
      <h2>Answer</h2>
      <p id="answer"></p>
      <h2>Evidence and citations</h2>
      <div id="evidence" class="evidence"></div>
      <h2>User evidence</h2>
      <div id="user-evidence" class="evidence"></div>
      <p id="disclaimer" class="disclaimer"></p>
    </section>
  </div>
`;

const form = document.querySelector('#query-form');
const question = document.querySelector('#question');
const files = document.querySelector('#files');
const selectedFiles = document.querySelector('#selected-files');
const responseLanguage = document.querySelector('#response-language');
const jurisdiction = document.querySelector('#jurisdiction');
const status = document.querySelector('#status');
const result = document.querySelector('#result');
let selectedFileList = [];

const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[character]));

function renderSelectedFiles() {
  selectedFiles.replaceChildren();
  if (!selectedFileList.length) {
    selectedFiles.textContent = 'No files selected.';
    return;
  }
  selectedFileList.forEach((file, index) => {
    const item = document.createElement('span');
    item.className = 'selected-file';
    item.textContent = file.name;
    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'remove-file';
    remove.textContent = 'Remove';
    remove.addEventListener('click', () => {
      selectedFileList = selectedFileList.filter((_, fileIndex) => fileIndex !== index);
      const dataTransfer = new DataTransfer();
      selectedFileList.forEach((selectedFile) => dataTransfer.items.add(selectedFile));
      files.files = dataTransfer.files;
      renderSelectedFiles();
    });
    item.append(' ', remove);
    selectedFiles.append(item);
  });
}

files.addEventListener('change', () => {
  selectedFileList = Array.from(files.files);
  renderSelectedFiles();
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const value = question.value.trim();
  if (!value) return;

  status.textContent = 'Loading…';
  status.className = 'status';
  result.hidden = true;
  form.querySelector('button').disabled = true;

  try {
    const formData = new FormData();
    formData.append('question', value);
    formData.append('response_language', responseLanguage.value);
    formData.append('jurisdiction', jurisdiction.value);
    selectedFileList.forEach((file) => formData.append('files', file));
    const response = await fetch(`${apiBaseUrl}/api/query`, {
      method: 'POST',
      ...(selectedFileList.length
        ? { body: formData }
        : {
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              question: value,
              response_language: responseLanguage.value,
              jurisdiction: jurisdiction.value,
            }),
          }),
    });
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.detail || `Request failed (${response.status})`);
    }
    const data = await response.json();
    document.querySelector('#question-display').textContent = `Question: ${value}`;
    document.querySelector('#classification').textContent = `Classification: ${data.classification.category} · Intent: ${data.classification.intent} · Confidence: ${Math.round(data.classification.confidence * 100)}%`;
    const providerLabel = data.provider === 'ollama'
      ? 'Ollama'
      : data.provider === 'fallback-demo'
        ? 'Fallback (demo)'
        : data.provider === 'none'
          ? 'No generation'
          : data.provider;
    const evidenceLabel = data.evidence_status === 'sufficient'
      ? 'Sufficient evidence'
      : 'Insufficient evidence';
    const confidenceLabel = data.grounded
      ? ` · Confidence: ${Math.round(data.confidence * 100)}%`
      : '';
    document.querySelector('#grounded').textContent = `${evidenceLabel} · Provider: ${providerLabel}${confidenceLabel}`;
    document.querySelector('#grounded').className = `grounded ${data.grounded ? 'grounded-yes' : 'grounded-no'}`;
    document.querySelector('#answer').textContent = data.answer;
    document.querySelector('#evidence').innerHTML = data.evidence.map((item) => `
      <article class="evidence-item">
        <strong>${item.title}</strong>
        <span>${item.source} · ${item.chunk_id}</span>
        <small>synthetic demo source — not authoritative</small>
        <p>${item.excerpt}</p>
      </article>
    `).join('') || '<p>No evidence was retrieved.</p>';
    document.querySelector('#user-evidence').innerHTML = data.user_evidence.map((item) => `
      <article class="evidence-item">
        <strong>${escapeHtml(item.filename)}</strong>
        <span>${escapeHtml(item.extraction_status)} · ${escapeHtml(item.media_type)} · ${item.file_size} bytes</span>
        <small>${item.extraction_status === 'image_pending'
          ? 'Image uploaded — visual analysis not yet available.'
          : item.extraction_status === 'extracted'
            ? 'Text extracted for this query only; not an authoritative source.'
            : item.extraction_status === 'image_only'
              ? 'PDF appears image-only — OCR is not available.'
              : 'This file was not used as extracted query context.'}</small>
      </article>
    `).join('') || '<p>No user files attached.</p>';
    document.querySelector('#disclaimer').textContent = data.disclaimer;
    result.hidden = false;
    status.textContent = '';
  } catch (error) {
    status.textContent = `Unable to reach the API. ${error.message}`;
    status.className = 'status error';
  } finally {
    form.querySelector('button').disabled = false;
  }
});
