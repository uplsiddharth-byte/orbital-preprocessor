# Brag plan — Orbital Scene Preprocessor (OSP)

Run: /brag → /brag-slim (Sonnet 5.5 hand-off). 60 s as requested (`--duration 60`), landscape 1920×1080 @ 30 fps, tone: **polished / cinematic mission-control, deadpan**.

## Answers
- **What is it?** Edge-AI pipeline that makes a satellite analyse a 6-band scene on board and downlink a ~1.2 KB JSON brief; a ground-side LLM analyst (RAG + episodic memory + deterministic policy) turns it into alerts and can task the satellite for a re-look.
- **Who / what for?** Orbital-compute (MOI-1A / OrbitLab) operators who pay for RF downlink and need maritime situational awareness.
- **Sets it apart:** brief instead of photo; SWIR bands for haze; LLM *advises*, rules *decide*; closed OVV loop; LLM-as-a-Judge faithfulness check.
- **Most impressive claim:** 100 MB scene → 1.2 KB brief (README headline ≈85,000:1).
- **Visual hook:** a giant "100 MB" collapsing into "1.2 KB" while a grid of 720 data cells dies except three ships.
- **Real UI shown:** the project's own Command Centre screenshot (`img.jpg`), the real demo payload, the real OVV request/response contract.
- **Share caption:** see `share-copy.txt`.

## Identity (from `ground/dashboard.py`)
Black, #f5f5f5 / #d4d4d4 / #8b8b8b, thin uppercase letter-spaced type, glass panels, monospace data. `background.jpg` used as base layer.

## Music (all on one 120 BPM grid, A minor, cuts on beats)
Drone + counter ticks → boom on the 100 MB→1.2 KB cut (2.5 s) → pad + plucks + riser → drop at 12 s (title) → kick/bass/claps/hats, arp from 17 s, 16th hats from 27 s → stripped for the OVV beat (51–54 s) → kick back → hit + Am resolve at 57 s. Blips on every on-screen cue, same key.

## Storyboard
| t (s) | Scene | On screen |
|---|---|---|
| 0–5 | Hook | "100 MB" counts up over a data grid → cut at 2.5 s to "1.2 KB", "≈ 85,000× smaller" |
| 5–12 | Problem | "Satellites are dumb cameras." / "They shoot 100 MB of ocean… then beam every byte home." / tile of empty water + crawling downlink bar |
| 12–17 | Reveal | ORBITAL SCENE PREPROCESSOR, "The satellite thinks before it speaks." |
| 17–27 | 01 See | B2 B3 B4 B8 B11 B12 chips; hazy visible tile vs SWIR tile; ship 87% / ship 79% / harbor 92% boxes |
| 27–36 | 02 Send | Real demo JSON types in; 100 MB bar vs 1.2 KB sliver; 85,000 : 1 counter |
| 36–44 | 03 Command Centre | Real dashboard screenshot, zoom to 2D map then Intelligence Feed |
| 44–51 | 04 Think | Retrieve / Remember / Reason / Decide cards; alert ladder |
| 51–57 | 05 Close the loop | OVV request → response (real contract); LLM-as-a-Judge: omission = fail, hallucination = fail |
| 57–60 | Punchline | "Don't downlink the ocean." + project URL |

## Things deliberately NOT claimed
- No detection accuracy / mAP: the repo trains on synthetic data with RGB-adapted weights (README non-goals).
- No on-orbit performance or latency number: the dashboard's 312 ms is a hard-coded demo value; the shipped telemetry shows 92–214 ms from a dev run.
- Demo coordinates/IDs are the repo's own synthetic payload.

## Voiceover + subtitles (added)
- **Voice:** Kokoro v1.0 (free, open-source neural TTS, run locally via `kokoro-onnx`), voice `am_michael`, speed 1.0. ElevenLabs was not usable in this session (host blocked, no API key).
- **Timing:** each line starts on a scene beat and is checked for overlap (`work/vo.py` → `vo_timings.json`). Music ducks ~7.5 dB under the voice (`work/mix.py`); final mix −14 LUFS, true peak −2.8 dBFS.
- **Subtitles:** burned into the video (overlay in `work/index.html`, cues in `work/subs.json`) and shipped as `brag.srt` / `brag.vtt`.
- **Files:** `brag.mp4` = voice + subtitles. `brag-no-voiceover.mp4` = the earlier music-only cut.
- Rebuild: `node work/render.js stills …` (writes cues.json) → `python work/audio.py` → `python work/vo.py` → `python work/mix.py` → `node work/render.js full` → ffmpeg. Needs Kokoro model files from the `kokoro-onnx` GitHub release `model-files-v1.0` (not committed).
