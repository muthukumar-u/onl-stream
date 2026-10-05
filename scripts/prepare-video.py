#!/usr/bin/env python3
"""Prepare a 720p30 H.264/AAC loop file locally, without broadcasting."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('input', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--force', action='store_true', help='Replace an existing output')
a = p.parse_args()
if not a.input.is_file(): p.error('Input file does not exist')
if a.input.resolve() == a.output.resolve(): p.error('Input and output must differ')
if a.output.exists() and not a.force: p.error('Output exists; choose another filename or use --force')
if not shutil.which('ffmpeg') or not shutil.which('ffprobe'): p.error('Install FFmpeg first')
probe = subprocess.run(['ffprobe','-v','error','-show_streams','-of','json',str(a.input)],capture_output=True,text=True,check=True)
streams = json.loads(probe.stdout)['streams']
if not any(s.get('codec_type') == 'video' for s in streams): p.error('Input has no video')
has_audio = any(s.get('codec_type') == 'audio' for s in streams)
a.output.parent.mkdir(parents=True,exist_ok=True)
with tempfile.NamedTemporaryFile(dir=a.output.parent,suffix='.mp4',delete=False) as temp:
    staged=Path(temp.name)
cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-nostdin','-i',str(a.input)]
if not has_audio: cmd += ['-f','lavfi','-i','anullsrc=r=44100:cl=stereo']
cmd += ['-map','0:v:0','-map','0:a:0' if has_audio else '1:a:0',
        '-vf','scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30',
        '-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p',
        '-b:v','8M','-minrate','8M','-maxrate','8M','-bufsize','16M',
        '-g','60','-keyint_min','60','-sc_threshold','0','-x264-params','nal-hrd=cbr:force-cfr=1',
        '-c:a','aac','-b:a','128k','-ar','44100','-ac','2','-shortest','-movflags','+faststart',str(staged)]
try:
    subprocess.run(cmd,check=True)
    staged.replace(a.output)
finally:
    staged.unlink(missing_ok=True)
print(f'Prepared {a.output}; no broadcast started.')
