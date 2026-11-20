(function () {
  'use strict';
  var buttons = { song: document.getElementById('typicalBirdsong'), call: document.getElementById('typicalBirdcall') };
  var caption = document.getElementById('typicalBirdsongCaption');
  var name = document.getElementById('modalCommon');
  var modal = document.getElementById('postcard-modal');
  var audio = new Audio(), selected = '', generation = 0, active = '', tracks = {}, needsUnlock = false;
  function stop() {
    audio.pause(); audio.removeAttribute('src'); audio.load(); active = '';
    Object.keys(buttons).forEach(function (kind) {
      buttons[kind].textContent = 'Typical ' + (kind === 'song' ? 'Song' : 'Call');
      buttons[kind].setAttribute('aria-pressed', 'false');
    });
  }
  function update() {
    var current = modal.getAttribute('aria-hidden') === 'false' ? name.textContent.trim() : '';
    if (current === selected) return;
    selected = current; var token = ++generation;
    stop(); tracks = {}; needsUnlock = false; caption.textContent = '';
    Object.keys(buttons).forEach(function (kind) { buttons[kind].disabled = true; });
    if (!current || current === '-') return;
    fetch('./avian/api/typical-birdsong.php?name=' + encodeURIComponent(current), { cache: 'no-store', credentials: 'same-origin' })
      .then(function (r) { if (!r.ok) { var error = new Error(); error.status = r.status; throw error; } return r.json(); })
      .then(function (result) {
        if (token !== generation) return;
        tracks = result.examples;
        var missing = [];
        Object.keys(buttons).forEach(function (kind) {
          buttons[kind].disabled = !tracks[kind].available;
          buttons[kind].title = tracks[kind].available ? tracks[kind].description : 'No separate ' + kind + ' example in this guide';
          if (!tracks[kind].available) missing.push(kind);
        });
        caption.textContent = 'Cornell Guide to Bird Sounds' + (missing.length ? ' · No separate ' + missing.join(' or ') + ' example available.' : '');
      }).catch(function (error) {
        if (token !== generation) return;
        needsUnlock = error.status === 401;
        Object.keys(buttons).forEach(function (kind) { buttons[kind].disabled = !needsUnlock; });
        caption.textContent = needsUnlock ? 'Unlock the menu to play reference sounds remotely. Tap either button to sign in.' : 'Reference library unavailable. Please try again.';
      });
  }
  Object.keys(buttons).forEach(function (kind) {
    buttons[kind].addEventListener('click', function () {
      if (needsUnlock) {
        var close = modal.querySelector('[data-postcard-close]');
        if (close) close.click();
        setTimeout(function () { document.getElementById('menuBtn').click(); }, 400);
        return;
      }
      if (active === kind && !audio.paused) { stop(); return; }
      stop(); document.dispatchEvent(new Event('avian-typical-play'));
      active = kind;
      audio.src = './avian/api/typical-birdsong.php?play=1&type=' + kind + '&name=' + encodeURIComponent(selected);
      buttons[kind].textContent = 'Stop ' + (kind === 'song' ? 'Song' : 'Call');
      buttons[kind].setAttribute('aria-pressed', 'true');
      caption.textContent = tracks[kind].description + ' · ' + tracks[kind].source;
      var token = generation;
      audio.play().catch(function (error) {
        if (error.name === 'AbortError' || token !== generation) return;
        stop(); caption.textContent = 'Could not play this example. Please try again.';
      });
    });
  });
  audio.addEventListener('ended', stop);
  audio.addEventListener('error', function () { if (audio.hasAttribute('src')) stop(); });
  document.addEventListener('avian-recording-play', stop);
  document.addEventListener('avian-reference-auth-change', function () { selected = ''; update(); });
  new MutationObserver(update).observe(name, { childList: true, subtree: true, characterData: true });
  new MutationObserver(update).observe(modal, { attributes: true, attributeFilter: ['aria-hidden'] });
})();
