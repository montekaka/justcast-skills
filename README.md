# JustCast skills

Podcast and audio editing skills for Codex, packaged as the **JustCast** plugin.

## Available skills

| Skill | What it does |
| --- | --- |
| `justcast:volume-control` | Measures loudness, recommends an adjustment, and creates a verified audio copy with FFmpeg. |

Volume Control preserves the original recording and exports MP3 by default. It asks before applying changes unless you enable automatic application. You can also choose a custom loudness target.

## Requirements

- Codex with local plugin support and access to a terminal.
- FFmpeg and ffprobe on your PATH. The skill checks for them and asks before installing anything missing.
- Local audio files you want to process.

The skill runs FFmpeg directly. It does not require a bundled server or API key. The command examples use a POSIX shell, as on macOS or Linux.

## Install

Clone or download this repository, then run these commands from its root:

```sh
codex plugin marketplace add .
codex plugin add justcast@justcast
```

Keep the repository folder in place because it is the local plugin source. Restart Codex if the skill does not appear in a new chat.

After this repository is hosted on GitHub, you can register its URL instead of a local folder:

```sh
codex plugin marketplace add https://github.com/OWNER/REPOSITORY.git
codex plugin add justcast@justcast
```

Replace `OWNER/REPOSITORY` with the actual GitHub owner and repository name. See the [official plugin packaging documentation](https://developers.openai.com/plugins/build/plugins) for supported installation surfaces.

## Use Volume Control

These are messages to send to Codex, not shell commands.

Set up your preferences:

```text
$justcast:volume-control init
```

Analyze a recording without changing it:

```text
$justcast:volume-control analyze "/path/to/episode.mp3"
```

Apply a specific target to a separate copy:

```text
$justcast:volume-control normalize "/path/to/episode.mp3" to -16 LUFS
```

Change a saved preference:

```text
$justcast:volume-control always apply the suggested adjustment when I ask to optimize audio
```

```text
$justcast:volume-control remember -18 LUFS as my default target
```

An analysis-only request never exports audio, even when automatic application is enabled. A target specified for one recording does not change your saved default unless you ask to remember it.

## Defaults

| Setting | Default |
| --- | --- |
| Approval | Ask before applying an adjustment |
| Integrated loudness | -16 LUFS |
| True-peak ceiling | -2 dBTP |
| Output | Separate MP3, using `libmp3lame -q:a 2` |

Less-negative LUFS values are louder. The peak ceiling leaves headroom. The skill measures the finished file and reports whether it meets the chosen target and ceiling.

Preferences are stored in `justcast-volume-control.json` under `CODEX_HOME`, or `~/.codex` when `CODEX_HOME` is unset. No personal preference file is included in this repository.

## How it works

FFprobe inspects the source, and FFmpeg measures the full recording. When a constant gain adjustment fits the peak ceiling, the skill uses FFmpeg's `volume` filter. When peak limiting is needed, it uses two-pass `loudnorm`. It measures the final encoded file again before reporting success.

The default name is `<source-stem>-normalized.mp3`. Existing files are not overwritten. Other output formats are supported when requested. Compatible metadata, cover art, and chapters need format-specific handling; the basic encoding example in the skill omits them.

## Repository layout

```text
.agents/plugins/marketplace.json
plugins/justcast/
  plugin.json
  skills/volume-control/
    SKILL.md
    agents/openai.yaml
```

The marketplace is named `justcast`. The plugin is also named `justcast`; its `volume-control` skill is exposed as `justcast:volume-control`.

To add another JustCast tool, add a focused skill under `plugins/justcast/skills/` and update this catalog. Keep personal audio, settings, and generated output out of the repository. Bump the plugin version when releasing changes.

## License

[MIT](LICENSE). Copyright (c) 2026 JustCast.

FFmpeg is installed separately and is governed by its own license.
