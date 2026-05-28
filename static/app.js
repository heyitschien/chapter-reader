const $ = (id) => document.getElementById(id);

const engineEl = $("engine");
const voiceEl = $("voice");
const speedEl = $("speed");
const speedVal = $("speedVal");
const stripMdEl = $("stripMd");
const textEl = $("text");
const playBtn = $("play");
const pauseBtn = $("pause");
const stopBtn = $("stop");
const statusEl = $("status");
const progressWrap = document.querySelector(".progress-wrap");
const progressEl = $("progress");
const progressLabel = $("progressLabel");
const engineNote = $("engineNote");

/** Paragraphs to pre-synthesize before playback starts. */
const WARMUP_CHUNKS = 2;
/** How many paragraphs ahead to keep synthesizing while you listen. */
const PREFETCH_AHEAD = 2;

let statusData = null;
let currentAudio = null;
let playing = false;
let paused = false;
let abortController = null;
/** @type {Map<number, Promise<Blob>>} */
let chunkCache = new Map();

speedEl.addEventListener("input", () => {
  speedVal.textContent = Number(speedEl.value).toFixed(2);
});

function setStatus(msg) {
  statusEl.textContent = msg;
}

function setControls({ play, pause, stop }) {
  playBtn.disabled = !play;
  pauseBtn.disabled = !pause;
  stopBtn.disabled = !stop;
}

function clearChunkCache() {
  chunkCache = new Map();
}

function b64ToBlob(b64, mime = "audio/wav") {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new Blob([bytes], { type: mime });
}

function playBlob(blob) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    currentAudio = audio;
    audio.onended = () => {
      URL.revokeObjectURL(url);
      currentAudio = null;
      resolve();
    };
    audio.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Audio playback failed"));
    };
    if (paused) {
      resolve();
      return;
    }
    audio.play().catch(reject);
  });
}

async function fetchStatus() {
  const res = await fetch("/api/status");
  if (!res.ok) throw new Error("Could not load engine status");
  statusData = await res.json();
  engineEl.innerHTML = "";
  const available = statusData.engines.filter((e) => e.available);
  if (!available.length) {
    engineNote.textContent =
      "No engine ready. Run ./setup.sh in this folder, then ./start.sh.";
    return;
  }
  for (const e of available) {
    const opt = document.createElement("option");
    opt.value = e.id;
    opt.textContent = e.name;
    engineEl.appendChild(opt);
  }
  if (statusData.default?.engine) {
    engineEl.value = statusData.default.engine;
  }
  populateVoices();
  const def = statusData.default;
  engineNote.textContent = def
    ? `Default: ${def.engine} · ${def.voice} (local, offline after first download)`
    : "Select an engine and voice.";
}

function populateVoices() {
  voiceEl.innerHTML = "";
  const eng = statusData.engines.find((e) => e.id === engineEl.value);
  if (!eng || !eng.voices?.length) {
    const opt = document.createElement("option");
    opt.value = eng?.default_voice || "";
    opt.textContent = eng?.default_voice || "default";
    voiceEl.appendChild(opt);
    return;
  }
  for (const v of eng.voices) {
    const opt = document.createElement("option");
    opt.value = v;
    opt.textContent = v;
    voiceEl.appendChild(opt);
  }
  if (eng.default_voice) voiceEl.value = eng.default_voice;
}

engineEl.addEventListener("change", populateVoices);

async function prepareChunks(text) {
  const res = await fetch("/api/prepare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, strip_md: stripMdEl.checked }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Prepare failed");
  }
  const data = await res.json();
  return data.chunks || [];
}

async function speakChunk(chunk, signal) {
  const res = await fetch("/api/speak", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: chunk,
      engine: engineEl.value,
      voice: voiceEl.value || null,
      speed: Number(speedEl.value),
      strip_md: false,
    }),
    signal,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Synthesis failed");
  }
  const data = await res.json();
  return b64ToBlob(data.audio_base64);
}

/** Start synthesis for chunk index if not already queued; returns cached promise. */
function prefetchChunk(chunks, index, signal) {
  if (index < 0 || index >= chunks.length) return null;
  if (!chunkCache.has(index)) {
    chunkCache.set(index, speakChunk(chunks[index], signal));
  }
  return chunkCache.get(index);
}

/** Queue synthesis for the next `count` paragraphs starting at `fromIndex`. */
function prefetchAhead(chunks, fromIndex, count, signal) {
  for (let i = fromIndex; i < Math.min(fromIndex + count, chunks.length); i++) {
    prefetchChunk(chunks, i, signal);
  }
}

async function warmupChunks(chunks, signal) {
  const n = Math.min(WARMUP_CHUNKS, chunks.length);
  if (n === 0) return;
  const jobs = [];
  for (let i = 0; i < n; i++) jobs.push(prefetchChunk(chunks, i, signal));
  await Promise.all(jobs);
}

function stopAll() {
  if (abortController) abortController.abort();
  abortController = null;
  playing = false;
  paused = false;
  clearChunkCache();
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  progressWrap.hidden = true;
  progressEl.value = 0;
  setControls({ play: true, pause: false, stop: false });
  setStatus("");
}

pauseBtn.addEventListener("click", () => {
  if (!playing || paused) return;
  paused = true;
  if (currentAudio) currentAudio.pause();
  setControls({ play: true, pause: false, stop: true });
  setStatus("Paused");
});

playBtn.addEventListener("click", async () => {
  if (paused && currentAudio) {
    paused = false;
    currentAudio.play();
    setControls({ play: false, pause: true, stop: true });
    setStatus("Playing…");
    return;
  }

  const text = textEl.value.trim();
  if (!text) {
    setStatus("Paste some text first.");
    return;
  }

  stopAll();
  playing = true;
  abortController = new AbortController();
  const { signal } = abortController;
  setControls({ play: false, pause: true, stop: true });
  progressWrap.hidden = false;

  try {
    setStatus("Preparing…");
    const chunks = await prepareChunks(text);
    if (!chunks.length) {
      setStatus("No speakable text.");
      stopAll();
      return;
    }
    const total = chunks.length;
    progressEl.max = total;

    const warmupCount = Math.min(WARMUP_CHUNKS, total);
    if (warmupCount > 0) {
      setStatus(
        warmupCount === 1
          ? "Warming up (first paragraph)…"
          : `Warming up (first ${warmupCount} paragraphs)…`,
      );
      await warmupChunks(chunks, signal);
      if (!playing || signal.aborted) return;
    }

    for (let i = 0; i < total; i++) {
      if (!playing || signal.aborted) break;

      prefetchAhead(chunks, i + 1, PREFETCH_AHEAD, signal);

      progressEl.value = i;
      progressLabel.textContent = `Paragraph ${i + 1} of ${total}`;

      const blobPromise = prefetchChunk(chunks, i, signal);
      const ready = chunkCache.has(i + 1);
      setStatus(
        ready
          ? `Playing ${i + 1}/${total}…`
          : `Playing ${i + 1}/${total} (buffering ahead)…`,
      );

      const blob = await blobPromise;
      if (!playing || signal.aborted) break;

      if (!paused) {
        setStatus(`Playing ${i + 1}/${total}…`);
      }
      await playBlob(blob);
    }

    if (playing && !signal.aborted) {
      progressEl.value = total;
      setStatus("Done.");
    }
  } catch (e) {
    if (e.name !== "AbortError") setStatus(String(e.message || e));
  } finally {
    playing = false;
    paused = false;
    clearChunkCache();
    setControls({ play: true, pause: false, stop: false });
  }
});

stopBtn.addEventListener("click", stopAll);

fetchStatus().catch((e) => {
  engineNote.textContent = e.message;
});
