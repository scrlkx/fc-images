# fc-images

Batch-converts WebP, AVIF, and JPEG images to PNG, then removes backgrounds using the [birefnet-general](https://github.com/ZhengPeng7/BiRefNet) AI model.

Installs as:
- **`fc-images`** — CLI command available system-wide
- **Nautilus right-click menu** — three actions on any directory (if Nautilus is installed)

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/scrlkx/fc-images/main/install.sh | bash
```

Requirements: Linux, Python 3.10+, git.

> **First run** downloads the birefnet-general model (~1 GB) to `~/.u2net/`. One-time only.

### Nautilus extension

Installed automatically if Nautilus and `nautilus-python` are present. If `nautilus-python` is missing, the installer prints the install command for your distro and asks you to re-run.

## Usage

```bash
# Convert formats + remove backgrounds (full pipeline)
fc-images /path/to/directory

# Convert formats only (WebP/AVIF/JPEG → PNG, keep backgrounds)
fc-images /path/to/directory --keep-background

# Remove backgrounds only (operates on existing PNGs)
fc-images /path/to/directory --backgrounds-only
```

Original files are deleted after conversion. Background removal overwrites PNGs in place.

## Update

Re-run the install command. Dependencies are only reinstalled if `requirements.txt` changed.

## Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/scrlkx/fc-images/main/install.sh | bash -s -- --uninstall
```

This removes `~/.local/bin/fc-images`, the Nautilus extension, and `~/.local/share/fc-images/`. The model cache at `~/.u2net/` is left in place — delete it manually if you no longer need it.

## Development

```bash
git clone https://github.com/scrlkx/fc-images
cd fc-images
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
make install-extension && make restart-nautilus
```
