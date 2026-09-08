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
        <button type="submit">Ask IP-SAKTI</button>
      </form>
      <p id="status" class="status" role="status"></p>
    </section>
    <section id="result" class="result" hidden>
      <div class="demo-label">DEMO / MOCK RESPONSE</div>
      <p id="question-display" class="question-display"></p>
      <p id="grounded" class="grounded"></p>
      <h2>Answer</h2>
      <p id="answer"></p>
      <h2>Evidence and citations</h2>
      <div id="evidence" class="evidence"></div>
      <p id="disclaimer" class="disclaimer"></p>
    </section>
  </div>
`;

const form = document.querySelector('#query-form');
const question = document.querySelector('#question');
const status = document.querySelector('#status');
const result = document.querySelector('#result');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const value = question.value.trim();
  if (!value) return;

  status.textContent = 'Loading…';
  status.className = 'status';
  result.hidden = true;
  form.querySelector('button').disabled = true;

  try {
    const response = await fetch(`${apiBaseUrl}/api/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: value }),
    });
    if (!response.ok) throw new Error(`Request failed (${response.status})`);
    const data = await response.json();
    document.querySelector('#question-display').textContent = `Question: ${value}`;
    document.querySelector('#grounded').textContent = data.grounded
      ? `Grounded answer · Provider: ${data.provider} · Confidence: ${Math.round(data.confidence * 100)}%`
      : `Not grounded · Provider: ${data.provider}`;
    document.querySelector('#grounded').className = `grounded ${data.grounded ? 'grounded-yes' : 'grounded-no'}`;
    document.querySelector('#answer').textContent = data.answer;
    document.querySelector('#evidence').innerHTML = data.evidence.map((item) => `
      <article class="evidence-item">
        <strong>${item.title}</strong>
        <span>${item.source} · ${item.chunk_id}</span>
        <p>${item.excerpt}</p>
      </article>
    `).join('') || '<p>No evidence was retrieved.</p>';
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
