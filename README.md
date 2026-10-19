# JustCast skills

Podcast and audio editing skills for Codex, packaged as the **JustCast** plugin.

## Available skills

| Skill | What it does |
| --- | --- |
| `justcast:volume-control` | Measures loudness, adjusts volume by percentage or loudness target, and creates a verified audio copy with FFmpeg. |

Volume Control preserves the original recording and exports MP3 by default. It asks before applying changes unless you enable automatic application. You can also choose a custom loudness target.

## Requirements

- Codex with local plugin support and access to a terminal.
- FFmpeg and ffprobe on your PATH. The skill checks for them and asks before installing anything missing.
- Local audio files you want to process.

The skill runs FFmpeg directly. It does not require a bundled server or API key. The command examples use a POSIX shell, as on macOS or Linux.

## Install

JustCast can be installed directly from GitHub before it is listed in the public plugin directory. These instructions use the [supported Codex plugin commands](https://learn.chatgpt.com/docs/cli/reference#codex-plugin).

### Install with one command

On macOS or Linux, install [Codex CLI](https://learn.chatgpt.com/docs/cli) and Git, then run:

```sh
curl -fsSL https://raw.githubusercontent.com/montekaka/justcast-skills/main/get.sh | bash
```

The script registers this repository as the `justcast` marketplace and installs `justcast@justcast` through Codex. Codex manages the downloaded files. The script checks for the required commands and stops if installation fails. It does not install FFmpeg.

Restart your desktop app and start a new chat, then send:

```text
$justcast:volume-control init
```

To review the installer before running it:

```sh
curl -fsSL https://raw.githubusercontent.com/montekaka/justcast-skills/main/get.sh -o get.sh
cat get.sh
bash get.sh
```

### Install manually

Run the same commands yourself:

```sh
codex plugin marketplace add https://github.com/montekaka/justcast-skills.git --ref main
codex plugin add justcast@justcast
```

For a local development copy, clone this repository and run `codex plugin marketplace add .` from its root, followed by `codex plugin add justcast@justcast`. Keep that folder in place because it is the local plugin source.

### Update or uninstall

To fetch changes from GitHub and reinstall the plugin:

```sh
codex plugin marketplace upgrade justcast
codex plugin add justcast@justcast
```

Restart your desktop app and start a new chat after updating.

To uninstall the plugin and remove its marketplace source:

```sh
codex plugin remove justcast@justcast
codex plugin marketplace remove justcast
```

Your saved Volume Control preferences and audio files remain in place.

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

Increase or decrease volume by a percentage:

```text
$justcast:volume-control increase the volume of "/path/to/episode.mp3" by 50%
```

```text
$justcast:volume-control decrease the volume of "/path/to/episode.mp3" by 25%
```

Percentages refer to audio amplitude. Increasing by 50% multiplies amplitude by 1.5, about +3.52 dB; decreasing by 50% multiplies it by 0.5, about -6.02 dB. These do not describe an equal percentage change in perceived loudness. You can also request "set volume to 50% of the original." Decreasing by 100% mutes the output; decreases above 100% are rejected.

The skill measures peaks before applying the adjustment. If the requested gain exceeds the peak ceiling, it asks whether to use limiting or a smaller gain. Percentage adjustments use the requested gain instead of the saved loudness target and leave saved preferences unchanged. Output names end in `-volume-adjusted.mp3`, or `-muted.mp3` for mute.

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
get.sh
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
