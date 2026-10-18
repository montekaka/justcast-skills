---
name: volume-control
license: MIT
description: Analyze podcast volume, recommend a level, and adjust audio with FFmpeg. Supports init setup, saved automatic application, and custom targets.
---

# JustCast Volume Control

Use FFmpeg and ffprobe directly. Route `init`, `setup`, or a request to configure defaults to the setup flow below. For audio work, ask for a file if none is supplied. Setup needs no audio file.

## Init

Invoke as `$justcast:volume-control init`. This is a conversational skill option, not an FFmpeg subcommand. Keep setup brief:

1. Introduce the skill in two or three sentences: it measures podcast loudness, suggests an adjustment, and uses FFmpeg to create and verify a separate copy while preserving the original. Explain that it asks before applying changes by default, saves MP3 output unless another format is requested, and supports automatic application or custom targets.
2. Check FFmpeg and ffprobe using the dependency rules below. Report availability and ask before installing anything missing. Preferences can still be configured if installation is declined.
3. Read existing preferences. Show their effective values, or the defaults below for a first setup. Ask the user to keep these settings or customize them. If they supplied their choices with `init`, use those choices without asking again.
4. For customization, collect approval mode (`ask` or `always`), target loudness in LUFS, and peak ceiling in dBTP together. Suggest -16 LUFS and -2 dBTP for new users; explain that less-negative LUFS values are louder and the peak ceiling leaves headroom. Keep existing values for settings the user does not change.
5. Validate the chosen settings, save them to the preference JSON, and read it back to verify. An `init` request authorizes saving the user's selected settings; do not ask for a second confirmation. If the user cancels or has not answered, do not save. Re-running `init` must preserve existing settings unless the user chooses changes; if existing JSON is invalid, show the issue and get replacement choices before overwriting it.
6. Confirm the saved defaults, any missing dependency, and give a short usage example: `$justcast:volume-control analyze /path/to/episode.mp3`. End setup without processing audio unless separately requested.

Normal audio requests can use defaults without running `init` first.

## Check tools and preferences

Run `command -v ffmpeg` and `command -v ffprobe`. If either is missing, ask permission before installing FFmpeg, specifying the package manager and command. The `always` preference does not authorize installation. Recheck after installation; report failures before trying another installer.

Read `${CODEX_HOME:-$HOME/.codex}/justcast-volume-control.json` if it exists. Missing fields use these defaults:

```json
{"mode":"ask","target_lufs":-16,"true_peak_dbtp":-2}
```

Read this as data, never source it as shell code. Accept `mode` values `ask` or `always`, finite target values from -70 to -5 LUFS, and finite peak ceilings from -9 to 0 dBTP. Report invalid settings before processing.

- In `ask` mode, show measurements and the suggested adjustment, then ask before changing audio. An explicit request to apply a specific adjustment already authorizes that operation.
- In `always` mode, apply the suggested or saved target when asked to optimize audio. Analysis-only requests always stop at the report.
- Per-file targets override saved targets for that run. Update the JSON only when asked to remember a preference, preserving other settings. A saved target does not change approval mode. Reset means restoring the defaults above.

Clarify ambiguous levels such as a volume percentage. The default is -16 LUFS; -2 dBTP leaves peak headroom. Honor custom or destination-specific targets. [Apple's podcast guidance](https://podcasters.apple.com/support/893-audio-requirements) recommends about -16 LKFS with peaks at or below -1 dBFS; this skill chooses an extra 1 dB of headroom.

## Analyze

Inspect streams, sample rate, channels, tags, and chapters:

```sh
ffprobe -v error -show_streams -show_format -show_chapters -of json "$INPUT"
```

Use absolute paths and quote them. For multiple audio streams or actual video, establish the intended track/workflow before proceeding. Keep mono/stereo channels unchanged; `dual_mono=false` measures native mono.

Measure the entire selected stream. Set `INPUT`, `TARGET`, and `PEAK` from the file and effective settings:

```sh
ffmpeg -hide_banner -nostdin -nostats -i "$INPUT" -map 0:a:0 \
  -af "loudnorm=I=${TARGET}:TP=${PEAK}:LRA=50:dual_mono=false:print_format=json" \
  -f null -
```

Read the JSON from stderr. Report `input_i` as integrated LUFS, `input_tp` as true peak dBTP, and `input_lra` as loudness range LU. Suggested gain in dB is `TARGET - input_i`. Projected peak is `input_tp + gain`. Stop on silence or non-finite measurements.

If loudness is within 1 LU of target and peaks meet the ceiling, recommend leaving it unchanged unless adjustment is explicitly requested. Otherwise recommend the gain and target. If projected peaks exceed the ceiling, explain that peak limiting may alter dynamics.

## Adjust and verify

After authorization, write a separate output with `-n` to refuse overwrites. Preserve the original. Use the environment's output directory when available. Unless the user explicitly specifies another output format, save an MP3 named `<source-stem>-normalized.mp3`, regardless of the input format. Do not ask for a format when it is unspecified.

When projected peaks fit the ceiling, prefer a constant gain with `-af "volume=${GAIN_DB}dB"`. It preserves dynamics. For example, this writes an MP3 copy with high-quality variable bitrate encoding. Set `OUTPUT` to a new `.mp3` path:

```sh
ffmpeg -hide_banner -nostdin -n -i "$INPUT" -map 0:a:0 \
  -map_metadata -1 -map_chapters -1 -af "volume=${GAIN_DB}dB" \
  -c:a libmp3lame -q:a 2 "$OUTPUT"
```

Use `libmp3lame -q:a 2` by default; honor an explicit bitrate or quality request. Keep the source channel count and sample rate when MP3 supports them; otherwise use a compatible sample rate such as 48 kHz. If the user requests another format, choose a compatible encoder and suitable quality. Preserve compatible tags, artwork, and chapters when needed; the basic example omits them. Remove or recalculate stale ReplayGain, R128 gain, and Sound Check metadata.

When peaks require limiting, use two-pass `loudnorm`. Reuse the analysis settings and pass `input_i`, `input_tp`, `input_lra`, `input_thresh`, and `target_offset` as `measured_I`, `measured_TP`, `measured_LRA`, `measured_thresh`, and `offset`, respectively. Set `linear=true`, retain `LRA=50`, and explicitly set `-ar` to the source sample rate or a rate supported by the output format because dynamic mode upsamples internally. FFmpeg may fall back to dynamic normalization. Consult local `ffmpeg -h filter=loudnorm` or [the filter documentation](https://ffmpeg.org/ffmpeg-filters.html#loudnorm) as needed.

Rerun the analysis command on the final encoded file, including MP3 or AAC outputs. Verify loudness within 1 LU of target and true peak within 0.1 dB of the chosen ceiling for measurement rounding. Show before/after values and link the output. If verification fails, label it as needing review; allow at most one corrective render from the original, then ask for direction. Never describe an unverified result as optimized.
