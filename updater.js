/* Self-updater: runs inside the Android app only. Checks latest.json, downloads a newer game bundle,
   and applies it on the next launch. A bundle that fails to start is rolled back automatically. */
(function () {
  const UPDATE_URL = '__UPDATE_URL__';
  const cap = window.Capacitor;
  if (!cap || !cap.isNativePlatform || !cap.isNativePlatform()) return;   // normal browser: nothing to do

  // audio/art packs are fetched from the patch site once, then cached
  if (UPDATE_URL.indexOf('__') !== 0) window.PACK_BASE = UPDATE_URL.replace(/[^/]*$/, '');

  const CU = cap.Plugins && cap.Plugins.CapacitorUpdater;
  if (!CU) return;

  // tells the updater this version started fine (otherwise it rolls back)
  CU.notifyAppReady().catch(() => {});

  if (!UPDATE_URL || UPDATE_URL.indexOf('__') === 0) return;   // placeholder not replaced: no update site
  setTimeout(checkForUpdate, 4000);

  function toast(text) {
    try {
      const d = document.createElement('div');
      d.textContent = text;
      d.style.cssText = 'position:fixed;left:50%;top:10px;transform:translateX(-50%);background:#000c;color:#fff;font:13px sans-serif;padding:8px 14px;border-radius:14px;z-index:99999;pointer-events:none';
      document.body.appendChild(d);
      setTimeout(() => d.remove(), 3500);
    } catch (e) { /* no DOM yet: skip the notice */ }
  }

  async function checkForUpdate() {
    try {
      const r = await fetch(UPDATE_URL + '?t=' + Date.now(), { cache: 'no-store' });
      if (!r.ok) return;
      const manifest = await r.json();
      const cur = await CU.current();
      const have = (cur && cur.bundle && cur.bundle.version) || 'builtin';
      if (!manifest.version || manifest.version === have) return;

      // already downloaded earlier: just mark it as the next bundle to load
      const list = await CU.list().catch(() => ({ bundles: [] }));
      const existing = (list.bundles || []).find(b => b.version === manifest.version);
      if (existing) { await CU.next({ id: existing.id }); return; }

      const b = await CU.download({
        url: new URL(manifest.url, UPDATE_URL).href,
        version: manifest.version,
        checksum: manifest.checksum,
      });
      await CU.next({ id: b.id });
      toast('Update ready – restart the game to get it');
    } catch (e) { /* offline or server unreachable: keep playing the current version */ }
  }
})();
