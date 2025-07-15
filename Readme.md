# Image Conversion Scripts for Waveshare e-Paper Photo Frames

These scripts help prepare images for display on [PhotoPainter](https://www.waveshare.com/wiki/PhotoPainter) or [PhotoPainter (B)](<https://www.waveshare.com/wiki/PhotoPainter_(B)>) e-paper frames.

## Prerequisites

- [ImageMagick](https://imagemagick.org/)

## Installation

You need the `imagemagick` package installed.

### Debian / Ubuntu

```bash
sudo apt update -y && sudo apt upgrade -y
sudo apt install imagemagick
```

### macOS (with Homebrew)

```bash
brew install imagemagick
```

## A Note on `convert` vs `magick`

Because of the author's WSL Debian version, the command `convert` is used instead of `magick`. You might want to change this in the script depending on your ImageMagick installation.

## Usage

For the arguments, refer to the "documentation" inside the script itself.
It can be printed by executing the script without any arguments.
```bash
./crop_and_convert.sh
```