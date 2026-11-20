(function () {
  'use strict';
  var button = document.getElementById('typicalBirdsong');
  var caption = document.getElementById('typicalBirdsongCaption');
  var name = document.getElementById('modalCommon');
  var modal = document.getElementById('postcard-modal');
  var audio = new Audio(), selected = '', generation = 0;
  function stop() {
    audio.pause(); audio.removeAttribute('src'); audio.load();
    button.textContent = 'Typical Birdsong'; button.setAttribute('aria-pressed', 'false');
  }
  function update() {
    var current = modal.getAttribute('aria-hidden') === 'false' ? name.textContent.trim() : '';
    if (current === selected) return;
    selected = current; var token = ++generation;
    stop(); button.disabled = true; caption.textContent = '';
    if (!current || current === '-') return;
    fetch('./avian/api/typical-birdsong.php?name=' + encodeURIComponent(current))
      .then(function (r) { if (!r.ok) throw new Error(); return r.json(); })
      .then(function (track) {
        if (token !== generation) return;
        button.disabled = false;
        caption.textContent = track.description + ' · ' + track.source;
      }).catch(function () { if (token === generation) caption.textContent = 'No local example available for this species.'; });
  }
  button.addEventListener('click', function () {
    if (!audio.paused) { stop(); return; }
    document.dispatchEvent(new Event('avian-typical-play'));
    audio.src = './avian/api/typical-birdsong.php?play=1&name=' + encodeURIComponent(selected);
    button.textContent = 'Stop Birdsong'; button.setAttribute('aria-pressed', 'true');
    audio.play().catch(function () { stop(); caption.textContent = 'Could not play this example. Please try again.'; });
  });
  audio.addEventListener('ended', stop);
  audio.addEventListener('error', function () { if (audio.hasAttribute('src')) stop(); });
  document.addEventListener('avian-recording-play', stop);
  new MutationObserver(update).observe(name, { childList: true, subtree: true, characterData: true });
  new MutationObserver(update).observe(modal, { attributes: true, attributeFilter: ['aria-hidden'] });
})();
