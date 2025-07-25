#!/usr/bin/env bash

# Immediately exit if any command fails
set -e

# --- Script Arguments ---
# $1: The path to the image (required)
# $2: The dither diffusion amount (optional, defaults to 85)
# $3: The adaptive blue reduction strength (optional, defaults to 0)
# $4: The saturation percentage (optional, defaults to 100)
# $5: The black level percentage (optional, defaults to 0)
# $6: The contrast adjustment (optional, defaults to 1)
# $7: The shadow brightening strength (optional, defaults to 0)
# $8: The dither method (optional, defaults to FloydSteinberg)

# Check if the first argument (image path) is empty
if [ -z "$1" ]; then
  echo "Usage: $0 <path_to_image> [diffusion_amount] [blue_reduction_strength] [saturation] [black_level] [contrast] [shadows] [dither_method]"
  echo ""
  echo "Example: $0 photo.jpg 90 1.5 110 10 3 5 FloydSteinberg"
  echo " $0 image.jpg 80 0 130 0 -2 2"
  # echo "$0 image.jpg 75 0 120 0 -4 6"
  # echo "$0 image.jpg 75 0 130 20 -4 3"
  echo ""
  echo "Processes an image for an 800x480 or 480x800 7-color e-ink display."
  echo "It auto-detects orientation, crops, resizes, and adjusts the image."
  echo ""
  echo "Saturation (default: 100):"
  echo "  A percentage. '100' is no change, '110' is 10% more saturated."
  echo ""
  echo "Black Level (default: 0):"
  echo "  A percentage (e.g., '5'-'15') to raise the output black level."
  echo "  This brightens the darkest parts of the image, making black into gray."
  echo "  '0' disables adjustment."
  echo ""
  echo "Contrast (default: 1):"
  echo "  A strength factor for non-linear contrast adjustment. The script handles"
  echo "  the conversion to the correct ImageMagick operator."
  echo "  - Positive values increase contrast (e.g., '4' is a good start)."
  echo "  - Negative values decrease contrast (e.g., '-4' for a moderate reduction)."
  echo "  - A value of '0' disables this adjustment."
  echo ""
  echo "Shadows (default: 0):"
  echo "  A strength factor ('3'-'7' is a good range) to brighten shadows by"
  echo "  reducing contrast only in the dark areas. '0' disables adjustment."
  echo ""
  echo "Dither Methods (default: FloydSteinberg):"
  echo "  FloydSteinberg - Good quality, the original error-diffusion dither."
  echo "  Riemersma      - Uses a Hilbert curve for a less structured look."
  echo "  None           - No dithering, just maps to the nearest color."
  echo ""
  echo "Blue Reduction (default: 0):"
  echo "  A strength factor (e.g., '1.0'-'3.0') to reduce blue in pixels"
  echo "  where blue is not the dominant color. '0' disables adjustment."
  echo "  You can visualize the effect of this parameter by running:"
  echo "  python plot_blue_reduction_effect.py [strength]"
  # echo "  FloydSteinberg - Good quality, the original error-diffusion dither."
  # echo "  Stucki         - Sharper and cleaner than Floyd-Steinberg, good for details."
  # echo "  Jarvis         - Softer and less grainy than Stucki, but can be slightly blurry."
  # echo "  Burkes         - Fast, produces a sharp, somewhat structured pattern."
  # echo "  Sierra3        - A larger, more complex filter, good at preserving tones."
  # echo "  None           - No dithering, just maps to the nearest color."
  exit 1
fi

mkdir -p converted

image="$1"
# Use the value of the 2nd argument ($2), or use 85 if it's not set
diffusion=${2:-85}
# Use the value of the 3rd argument ($3), or use 0 if it's not set
blue_reduction_strength=${3:-0}
# Use the value of the 4th argument ($4), or use 100 if it's not set
saturation=${4:-100}
# Use the value of the 5th argument ($5), or use 0 if it's not set
black_level=${5:-0}
# Use the value of the 6th argument ($6), or use 1 if it's not set
contrast=${6:-1}
# Use the value of the 7th argument ($7), or use 0 if it's not set
shadows=${7:-0}
# Use the value of the 8th argument ($8), or use FloydSteinberg if it's not set
dither_method=${8:-FloydSteinberg}

output_path=./converted/"${image%.*}_converted.bmp"

echo "Processing '$image' -> '$output_path' (Dither: ${dither_method}, Diffusion: ${diffusion}%, Saturation: ${saturation}%, Black Level: ${black_level}%, Contrast: ${contrast}, Shadows: ${shadows}, Blue Reduction: ${blue_reduction_strength})"

# Get image dimensions to determine orientation
width=$(identify -format "%w" "$image")
height=$(identify -format "%h" "$image")

echo "Original dimensions: ${width}x${height}"

# Determine orientation and set crop ratio and final dimensions
if [ "$width" -gt "$height" ]; then
    # Landscape orientation
    crop_ratio="5:3"
    final_dimensions="800x480"
    orientation="landscape"
else
    # Portrait orientation
    crop_ratio="3:5"
    final_dimensions="480x800"
    orientation="portrait"
fi

echo "Detected $orientation orientation, cropping to $crop_ratio and scaling to $final_dimensions"

# Prepare options for image adjustment
adjustment_ops=()
if [ "$blue_reduction_strength" != "0" ]; then
    k=${blue_reduction_strength}

    # Define the components of the -fx expression
    # x is the ratio of blue in the pixel
    # blue_reduction_scaler is a function of x that determines how much to scale the blue channel
    # The final expression scales the blue channel (u.b) by this scaler.
    fx_expression=" \
        k = ${k}; \
        ratio = u.b / (u.r + u.g + u.b + 0.000001); \
        result = ((1/4)*(-4*pi^2*exp(3*ratio) + 6*pi*sin(2*pi*ratio) - 9*cos(2*pi*ratio) + 9 + 4*pi^2)*exp(3 - 3*ratio)/(pi^2*(1 - exp(3)))-1)*k+1; \
        result * u.b \
    "
    
    # Explicitly convert to RGB color space first to ensure proper channel separation
    adjustment_ops+=(-colorspace RGB -channel B -fx "$fx_expression" -channel RGB)
fi
if [ "$black_level" != "0" ]; then
    # Raise the output black level to brighten shadows.
    # For example, a value of '10' makes pure black 10% gray.
    adjustment_ops+=("+level" "${black_level}%")
fi
if [ "$shadows" != "0" ]; then
    # Brighten shadows by decreasing contrast in the dark tones (e.g., centered at 25%).
    # The 'shadows' variable acts as the strength. '3' to '7' is a good range.
    adjustment_ops+=("+sigmoidal-contrast" "${shadows}x25%")
fi
if [ "$contrast" != "0" ]; then
    # For sigmoidal-contrast, '-' increases contrast, '+' decreases it.
    # The strength value should always be positive.
    if (( $(echo "$contrast < 0" | bc -l) )); then
        # Contrast is negative, so decrease contrast.
        abs_contrast=${contrast#-} # Get absolute value
        adjustment_ops+=("+sigmoidal-contrast" "${abs_contrast}x50%")
    else
        # Contrast is positive, so increase contrast.
        adjucstment_ops+=("-sigmoidal-contrast" "${contrast}x50%")
    fi
fi
if [ "$saturation" != "100" ]; then
    adjustment_ops+=(-modulate "100,${saturation}")
fi

# 1. Crop, scale, and adjust the original image in one step
convert "$image" \
    -gravity center \
    -crop "$crop_ratio" \
    -resize "$final_dimensions!" \
    "${adjustment_ops[@]}" \
    "$output_path"

# 2. Dither the newly processed image, overwriting it
#    The diffusion amount and dither method are now set by our variables
convert "$output_path" \
    -dither "${dither_method}" \
    -define "dither:diffusion-amount=${diffusion}%" \
    -remap palette_7color.gif \
    -type truecolor \
    BMP3:"$output_path"

# Clean up any temporary files at the end
if [[ -n "${temp_image:-}" && -f "$temp_image" ]]; then
    rm -f "$temp_image"
fi

echo "Done."