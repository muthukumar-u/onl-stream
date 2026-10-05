#!/usr/bin/env python3
"""Loop a pre-encoded video to YouTube, without printing stream credentials."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video', default='/opt/youtube-stream/live.mp4')
    parser.add_argument('--env-file', default='/etc/youtube-stream/stream.env')
    parser.add_argument('--check', action='store_true', help='Validate locally without broadcasting')
    args = parser.parse_args()
    video = Path(args.video)
    if not video.is_file() or not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        sys.exit('Install FFmpeg and provide an existing video file.')
    try:
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(video)], capture_output=True, check=True, text=True)
        streams = json.loads(result.stdout)['streams']
    except (subprocess.SubprocessError, ValueError, KeyError):
        sys.exit('Could not read the video.')
    v = next((s for s in streams if s['codec_type'] == 'video'), {})
    a = next((s for s in streams if s['codec_type'] == 'audio'), {})
    if v.get('codec_name') != 'h264' or a.get('codec_name') != 'aac':
        sys.exit('Use a pre-encoded H.264 video with an AAC audio track.')
    if args.check:
        print(f"Local check passed: {v['width']}x{v['height']}, {v['r_frame_rate']} fps, H.264/AAC. No broadcast started.")
        return
    try:
        values = {}
        for line in Path(args.env_file).read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#'):
                key, value = line.split('=', 1)
                values[key.strip()] = value.strip()
        url = values['YOUTUBE_RTMPS_URL']
        parsed = urlsplit(url)
        if parsed.scheme != 'rtmps' or parsed.hostname != 'a.rtmps.youtube.com' or not parsed.path.startswith('/live2/') or not parsed.path.removeprefix('/live2/') or parsed.query or parsed.fragment or parsed.username or parsed.password or 'YOUR_STREAM_KEY' in url:
            raise ValueError()
    except (OSError, KeyError, ValueError):
        sys.exit('Set a valid primary YouTube RTMPS URL in the private configuration file.')
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin',
               '-re', '-stream_loop', '-1', '-i', str(video),
               '-map', '0:v:0', '-map', '0:a:0', '-c', 'copy',
               '-flvflags', 'no_duration_filesize', '-rw_timeout', '30000000',
               '-f', 'flv', url]
    print('Sending the video to YouTube. Check stream health in YouTube Studio.', flush=True)
    # FFmpeg can include the destination key in error messages. Do not log it.
    try:
        child = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except KeyboardInterrupt:
        return
    print(f'Encoder stopped (exit code {child.returncode}).', flush=True)
    sys.exit(child.returncode)


if __name__ == '__main__':
    main()
