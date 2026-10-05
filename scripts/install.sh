#!/usr/bin/env bash
set -euo pipefail
if [[ $EUID -ne 0 ]]; then echo 'Run with sudo on Ubuntu 22.04/24.04.' >&2; exit 1; fi
if systemctl is-active --quiet youtube-stream.service; then
  echo 'Stop youtube-stream.service before updating an existing installation.' >&2; exit 1
fi
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
video_file="${1:-$repo_dir/media/live.mp4}"
if [[ ! -f "$video_file" ]]; then echo 'Supply a prepared MP4: sudo bash scripts/install.sh /path/to/live.mp4' >&2; exit 1; fi
apt-get update
apt-get install -y ffmpeg python3
python3 "$repo_dir/scripts/stream.py" --check --video "$video_file"
if ! id -u media-stream >/dev/null 2>&1; then
  useradd --system --user-group --shell /usr/sbin/nologin media-stream
fi
install -d -m 755 /opt/youtube-stream
install -d -m 750 -o root -g media-stream /etc/youtube-stream
install -m 644 "$repo_dir/scripts/stream.py" /opt/youtube-stream/stream.py
install -m 644 "$video_file" /opt/youtube-stream/live.mp4
if [[ ! -e /etc/youtube-stream/stream.env ]]; then
  install -m 640 -o root -g media-stream "$repo_dir/.env.example" /etc/youtube-stream/stream.env
fi
install -m 644 "$repo_dir/deploy/youtube-stream.service" /etc/systemd/system/youtube-stream.service
systemctl daemon-reload
printf '%s\n' 'Installed without starting or enabling broadcasting.' 'Edit /etc/youtube-stream/stream.env privately, then follow README.md.'
