(function(){const o=document.createElement("link").relList;if(o&&o.supports&&o.supports("modulepreload"))return;for(const e of document.querySelectorAll('link[rel="modulepreload"]'))t(e);new MutationObserver(e=>{for(const r of e)if(r.type==="childList")for(const i of r.addedNodes)i.tagName==="LINK"&&i.rel==="modulepreload"&&t(i)}).observe(document,{childList:!0,subtree:!0});function n(e){const r={};return e.integrity&&(r.integrity=e.integrity),e.referrerPolicy&&(r.referrerPolicy=e.referrerPolicy),e.crossOrigin==="use-credentials"?r.credentials="include":e.crossOrigin==="anonymous"?r.credentials="omit":r.credentials="same-origin",r}function t(e){if(e.ep)return;e.ep=!0;const r=n(e);fetch(e.href,r)}})();const u="http://localhost:8000";document.querySelector("#app").innerHTML=`
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
`;const d=document.querySelector("#query-form"),l=document.querySelector("#question"),s=document.querySelector("#status"),c=document.querySelector("#result");d.addEventListener("submit",async a=>{a.preventDefault();const o=l.value.trim();if(o){s.textContent="Loading…",s.className="status",c.hidden=!0,d.querySelector("button").disabled=!0;try{const n=await fetch(`${u}/api/query`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:o})});if(!n.ok)throw new Error(`Request failed (${n.status})`);const t=await n.json();document.querySelector("#question-display").textContent=`Question: ${o}`,document.querySelector("#grounded").textContent=t.grounded?`Grounded answer · Provider: ${t.provider} · Confidence: ${Math.round(t.confidence*100)}%`:`Not grounded · Provider: ${t.provider}`,document.querySelector("#grounded").className=`grounded ${t.grounded?"grounded-yes":"grounded-no"}`,document.querySelector("#answer").textContent=t.answer,document.querySelector("#evidence").innerHTML=t.evidence.map(e=>`
      <article class="evidence-item">
        <strong>${e.title}</strong>
        <span>${e.source} · ${e.chunk_id}</span>
        <p>${e.excerpt}</p>
      </article>
    `).join("")||"<p>No evidence was retrieved.</p>",document.querySelector("#disclaimer").textContent=t.disclaimer,c.hidden=!1,s.textContent=""}catch(n){s.textContent=`Unable to reach the API. ${n.message}`,s.className="status error"}finally{d.querySelector("button").disabled=!1}}});
