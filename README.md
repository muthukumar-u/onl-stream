# Keep a video playing live on YouTube

## What is this for?

This kit sends one video file from your server to YouTube. When the video ends, it starts again. It can keep going while your Mac is off.

The broadcast is live, but the animation is a prerecorded video. Say this clearly in your stream description.

## Why use it?

The server sends an already prepared video instead of creating each picture again while streaming. This keeps the server's work low. It also tries to restart the sender if it stops unexpectedly.

## What do I need?

- A working Ubuntu 22.04 or 24.04 server.
- A way to log in to it, such as the Tailscale kit.
- YouTube live streaming enabled for your channel.
- An MP4 video. Make one using the separate animation kit, or use your own.

This kit is reusable for different channels. Your channel's private details are added only when you install it.

## Step 1 — Prepare the video

**Where:** your Mac.

If you generated `live.mp4` using the animation kit, it is already prepared. Skip conversion and copy it in Step 2.

For your own video, open Terminal in the `youtube-streaming` folder. If the unzipped folder is in Downloads:

```bash
cd ~/Downloads/youtube-streaming
```

Install the video tool and Python if you do not already have them. This command uses Homebrew, a tool for installing programs on a Mac:

```bash
brew install ffmpeg python
```

If Terminal says `brew` is missing, first follow the installation instructions at https://brew.sh, then reopen Terminal.

Put your source video in this kit's folder and name it `input.mp4`, or use its actual path in the command:

```bash
python3 scripts/prepare-video.py input.mp4 media/live.mp4
```

**What it does:** makes a copy suitable for the stream. The picture is 720p at 30 frames per second. Existing sound is kept; a silent sound track is added if there is no sound.
**Why:** YouTube needs a compatible video and sound format. The tool does not edit the ending to match the beginning, so choose a video that repeats pleasantly.

Check it:

```bash
python3 scripts/stream.py --check --video media/live.mp4
```

**What should happen:** it prints “Local check passed.” This checks the file, without sending it to YouTube. Also play the video yourself and check the picture and sound.

## Step 2 — Copy the kit and video to your server

**Where:** Mac Terminal.

These commands assume you saved the `stream-server` login shortcut from the Tailscale kit:

```bash
scp -r ~/Downloads/youtube-streaming stream-server:~/
```

**What it does:** copies the setup files to the server.

Now copy your video. Choose ONE of these commands, depending on where you made it.

If you prepared your own video in Step 1:

```bash
scp ~/Downloads/youtube-streaming/media/live.mp4 stream-server:~/live.mp4
```

If you used the animation kit:

```bash
scp ~/Downloads/visual-loop-generator/media/live.mp4 stream-server:~/live.mp4
```

Then log in:

```bash
ssh stream-server
```

## Step 3 — Install the streaming setup

**Where:** the Terminal window connected to your server.

```bash
cd ~/youtube-streaming
sudo bash scripts/install.sh ~/live.mp4
```

**What it does:** installs the video tool, copies your video into its working folder, and prepares a background program called `youtube-stream`.
**Why:** a background program keeps running when you close Terminal. It can also start after a server reboot.

**What should happen:** the installer says the setup is installed. Streaming has not started yet.

If you are updating an existing installation, stop the stream first using the command in “Stop the stream” below.

## Step 4 — Add your YouTube stream key

**Where:** YouTube Studio in your Mac browser, then your server Terminal.

1. Open https://studio.youtube.com.
2. Choose **Create → Go live → Stream**.
3. Find the server address and **stream key**. A stream key is a private password that lets your server send video to your channel.

Open the private settings file on your server:

```bash
sudoedit /etc/youtube-stream/stream.env
```

**What it does:** opens the file where the sender reads your YouTube destination.

Replace `YOUR_STREAM_KEY` with the key from Studio. Keep this format, with no spaces:

```text
YOUTUBE_RTMPS_URL=rtmps://a.rtmps.youtube.com:443/live2/YOUR_STREAM_KEY
```

The address before the key is YouTube's primary secure streaming address. This kit accepts that address. `RTMPS` simply means the video is sent through an encrypted connection.

Save and close the editor. If it opens **nano**, press Control+O, then Enter to save, and Control+X to close. If it opens **vi/vim**, press `i` to edit, then Escape, type `:wq`, and press Enter to save and close.

Keep the real key in this private server file. Leave the example file in your GitHub copy unchanged.

## Step 5 — Try an unlisted stream first

**Where:** YouTube Studio and your server Terminal.

An **unlisted** stream can be watched by people with its link, but it does not normally appear in search. It is useful for testing.

In Studio, choose Unlisted and Normal latency. Latency means the delay between sending a picture and viewers seeing it. Keep Auto-start and Auto-stop off for this first test so you control when the event begins and ends.

If Studio also makes a vertical version, inspect its preview. Turn off Dual stream if that version cuts off your animation or text.

On the server, start sending the video:

```bash
sudo systemctl start youtube-stream
```

**What it does:** starts the background sender. `systemctl` is Ubuntu's tool for controlling background programs.

Check whether it is running:

```bash
sudo systemctl status youtube-stream --no-pager
```

**What should happen:** you see `active (running)`. In Studio, a preview of your video should appear. Click **Go live** to begin the unlisted event.

Watch for at least 15 minutes. Check playback on another device and look for warnings in Studio's Stream Health panel. The server saying “running” is not enough to prove viewers can watch.

## Step 6 — Use it for your normal stream

After the test works, choose your intended visibility in Studio and start the event. To let the sender start again after the server reboots:

```bash
sudo systemctl enable youtube-stream
```

**What it does:** remembers to start the sender when the server starts.
**Why:** you will not need to log in just to start it after every reboot.

YouTube may still need you to click Go live, depending on the event settings. Check Studio after an outage, especially if the earlier event ended.

## Commands for later

**Where:** your server Terminal.

| What you want | Command | What happens |
| --- | --- | --- |
| Start sending video | `sudo systemctl start youtube-stream` | Starts the sender now. |
| Check it | `sudo systemctl status youtube-stream --no-pager` | Shows whether the sender is running. |
| Restart it | `sudo systemctl restart youtube-stream` | Stops and starts it again. |
| Stop the stream | `sudo systemctl stop youtube-stream` | Stops sending video now. Also end the event in Studio. |
| Stop now and keep it off after reboots | `sudo systemctl disable --now youtube-stream` | Stops it and removes automatic startup. |
| Read recent messages | `sudo journalctl -u youtube-stream -n 30 --no-pager` | Shows the sender's recent activity. |

Closing Terminal does not stop the stream. Stopping the stream does not delete the cloud server or stop any server charges.

## Change the video later

**Where:** first your Mac, then your server.

From your Mac, copy the new video using its actual location:

```bash
scp ~/Downloads/next.mp4 stream-server:~/next.mp4
```

On the server, check it before replacing the working video:

```bash
python3 /opt/youtube-stream/stream.py --check --video ~/next.mp4
```

Only continue if the check passes:

```bash
sudo systemctl stop youtube-stream
sudo cp /opt/youtube-stream/live.mp4 /opt/youtube-stream/previous.mp4
sudo install -m 644 ~/next.mp4 /opt/youtube-stream/live.mp4
sudo systemctl start youtube-stream
```

**What these do:** stop the sender, save the old video, replace it, and start again. Viewers may see a short interruption.

If the new video causes trouble, restore the old one:

```bash
sudo systemctl stop youtube-stream
sudo install -m 644 /opt/youtube-stream/previous.mp4 /opt/youtube-stream/live.mp4
sudo systemctl start youtube-stream
```

## If something does not work

| Problem | What to check |
| --- | --- |
| No preview in Studio | Live access is enabled, the correct stream is selected, and the key is correct. |
| Sender keeps stopping | Stop it, run the file check, and read recent messages using the table above. Also check Studio. |
| File check fails | Prepare the video again using Step 1. |
| No sound | The animation kit intentionally creates a silent video. Use your own audio if you want sound. |
| Black bars | Your source has a different picture shape. A wide 16:9 source fills the output better. |

The sender retries after it stops unexpectedly. It cannot reopen a YouTube event that has ended, or keep running if the cloud server is unavailable.

## How much internet data does it use?

With the included settings, 30 days of continuous streaming sends about **2.63 TB**, plus a little extra for the connection. This is the server's outgoing data, not your Mac's data.

Check how much outgoing data your cloud plan includes before leaving it running all month.

## What are the files?

| File | What it is for |
| --- | --- |
| `scripts/prepare-video.py` | Converts your video into a suitable format. |
| `scripts/stream.py` | Checks the video or sends it repeatedly to YouTube. |
| `scripts/install.sh` | Sets up the sender on the server. |
| `deploy/youtube-stream.service` | Tells Ubuntu how to run the sender in the background. |
| `.env.example` | Example settings with a fake stream key. |
| `.gitignore` | Helps Git skip private settings, videos, and key files. |
| `LICENSE` | Explains permission to reuse and share the code. It is not a setup step. |

Keep the server limited to people you trust. If your stream key becomes public, reset it in Studio, update the private settings file, and restart the sender.

More help: https://support.google.com/youtube/answer/2853702?hl=en
