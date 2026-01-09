# yt-dlp Downloader GUI v1.4.x

![Preview](https://raw.githubusercontent.com/bluesjamgt/yt-dlp-gui/17c443ef710a5bf0576a1d09c69e75d0f3d7d967/preview.jpg)

A lightweight, standalone graphical interface for [yt-dlp](https://github.com/yt-dlp/yt-dlp). Designed for streamlined media extraction without command-line interaction.

## ◼ System Overview

This utility automates the execution of `yt-dlp` commands through a user-friendly interface. It includes a pre-packaged FFmpeg environment, allowing for immediate deployment without external dependency configuration.

## ◼ Features

* **Media Extraction**: Supports high-resolution video (up to 2160p) in MP4/MKV and audio extraction in MP3/M4A formats.
* **Subtitle Mode**: [v1.4.10] standalone execution for retrieving and converting subtitles to SRT format.
* **Batch Processing**: Automated parsing and downloading of full playlists.
* **Portable Architecture**: Single-file executable (`.exe`) with embedded FFmpeg/FFprobe binaries. No installation required.
* **History Log**: Local tracking of downloaded URLs to prevent redundancy.

## ◼ Installation & Usage

1. Navigate to the **[Releases](https://github.com/bluesjamgt/yt-dlp-gui/releases/latest)** section.
2. Download the latest executable binary (`.exe`).
3. Run the application.
    * *Note: Configuration files (`config.json`) will be automatically generated in the execution directory.*

## ◼ Requirements

* **OS**: Windows 10/11
* **Dependencies**: None (All necessary binaries are bundled).

## ◼ Legal & License

* **Purpose**: This software is intended for technical research and personal archiving purposes only.
* **Core**: Powered by **yt-dlp**.
* **Transcoding**: Includes **FFmpeg** binaries (Licensed under LGPL/GPL). All rights belong to the respective developers.
* **Compliance**: Users bear full responsibility for complying with copyright laws and the terms of service of the source platforms.

## ◼ Credits

* **Development**: Bluz J & AI Assistant
