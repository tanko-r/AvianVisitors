(function () {
  'use strict';
  var button = document.getElementById('helpButton');
  var dialog = document.getElementById('helpDialog');
  var form = document.getElementById('suggestionForm');
  var text = document.getElementById('suggestionText');
  var status = document.getElementById('suggestionStatus');
  var sending = false;
  var test = document.getElementById('touchTest');
  var target = document.getElementById('touchTarget');
  var note = document.getElementById('touchTestNote');
  var points = [[.12,.15],[.88,.15],[.5,.5],[.12,.85],[.88,.85]], samples = [], targetAt;
  function nextTarget() {
    var point = points[samples.length];
    target.hidden = !point;
    if (!point) {
      var dx = samples.reduce(function(s,p){return s+p.dx;},0)/samples.length;
      var dy = samples.reduce(function(s,p){return s+p.dy;},0)/samples.length;
      var max = Math.max.apply(null,samples.map(function(p){return Math.hypot(p.dx,p.dy);}));
      note.textContent = 'Finished. Average offset: ' + dx.toFixed(1) + ' px right, ' + dy.toFixed(1) + ' px down. Largest miss: ' + max.toFixed(1) + ' px. ' + (max <= 18 ? 'Alignment looks reasonable.' : 'Repeat carefully; consistent misses may indicate scaling or touch alignment trouble.');
      window.__avianTouchTest = { samples: samples.slice(), dx: dx, dy: dy, max: max };
      return;
    }
    targetAt = { x: innerWidth*point[0], y: innerHeight*point[1] };
    target.style.left = targetAt.x+'px'; target.style.top = targetAt.y+'px';
    note.textContent = 'Tap the center of target ' + (samples.length+1) + ' of 5. Close is always available in the top right.';
  }
  document.getElementById('touchTestStart').addEventListener('click', function () {
    samples = []; test.showModal(); nextTarget();
  });
  document.getElementById('touchTestClose').addEventListener('click', function () { test.close(); });
  test.addEventListener('pointerdown', function (event) {
    if (event.target.closest('button') || samples.length >= points.length) return;
    event.preventDefault();
    samples.push({ dx: event.clientX-targetAt.x, dy: event.clientY-targetAt.y, x: event.clientX, y: event.clientY });
    nextTarget();
  });
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
