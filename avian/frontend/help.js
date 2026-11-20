(function () {
  'use strict';
  var button = document.getElementById('helpButton');
  var dialog = document.getElementById('helpDialog');
  var form = document.getElementById('suggestionForm');
  var text = document.getElementById('suggestionText');
  var status = document.getElementById('suggestionStatus');
  var sending = false;
  button.addEventListener('click', function () { if (!dialog.open) dialog.showModal(); });
  document.getElementById('helpClose').addEventListener('click', function () { dialog.close(); });
  dialog.addEventListener('close', function () { button.focus({ preventScroll: true }); });
  form.addEventListener('submit', function (event) {
    event.preventDefault();
    if (sending) return;
    var suggestion = text.value.trim();
    if (!suggestion) { status.textContent = 'Please write your suggestion first.'; text.focus(); return; }
    sending = true;
    var send = form.querySelector('button[type="submit"]');
    send.disabled = true;
    status.textContent = 'Saving…';
    fetch('./avian/api/suggestions.php', {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-Avian-Suggestion': '1' },
      body: JSON.stringify({ suggestion: suggestion })
    }).then(function (response) {
      return response.json().then(function (result) {
        if (!response.ok || !result.ok) throw new Error(result.error || 'Could not save your suggestion.');
      });
    }).then(function () {
      text.value = '';
      status.textContent = 'Thank you! Your suggestion is on the improvement list.';
    }).catch(function () {
      status.textContent = 'Could not save right now. Please use the home-network site and try again. Your text is still here.';
    }).then(function () { sending = false; send.disabled = false; });
  });
})();
