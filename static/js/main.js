// Brasil Soberano — JavaScript

// Simulador: vote em cenário
function vote(scenarioId, option) {
  const card = document.getElementById('scenario-' + scenarioId);
  const result = card.querySelector('.scenario-result');
  const btnA = card.querySelector('.option-a');
  const btnB = card.querySelector('.option-b');
  
  btnA.classList.remove('selected-a');
  btnB.classList.remove('selected-b');
  if (option === 'a') btnA.classList.add('selected-a');
  else btnB.classList.add('selected-b');

  fetch('/simulador/vote', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({scenario_id: scenarioId, vote: option})
  })
  .then(r => r.json())
  .then(data => {
    let html = '<h4>📜 O que realmente aconteceu:</h4>';
    html += '<p>' + data.what_happened + '</p>';
    html += '<h4 style="margin-top:12px;color:#1565C0">📊 Consequência:</h4>';
    html += '<p>' + data.consequence + '</p>';
    html += '<div class="scenario-lesson">💡 <strong>Lição:</strong> ' + data.lesson + '</div>';
    result.innerHTML = html;
    result.classList.add('show');
    result.scrollIntoView({behavior:'smooth', block:'nearest'});
  });
}

// Filtro de estados
function filterStates(query) {
  const cards = document.querySelectorAll('.state-card');
  query = query.toLowerCase();
  cards.forEach(card => {
    const text = card.textContent.toLowerCase();
    card.style.display = text.includes(query) ? '' : 'none';
  });
}
