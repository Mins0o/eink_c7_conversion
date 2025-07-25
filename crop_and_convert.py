#!/usr/bin/env python3

import sys
import os
import argparse
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
import math

def reduce_blue_in_pixel(r, g, b, strength, dark_strength=0, luminance_threshold=0.35):
    """
    Reduce blue in a pixel based on blue dominance and darkness.
    
    Args:
        r, g, b: RGB values (0-255)
        strength: Blue reduction strength for non-blue-dominant pixels
        dark_strength: Additional blue reduction strength for dark pixels
        luminance_threshold: Threshold below which pixels are considered dark
    """
    if strength == 0 and dark_strength == 0:
        return r, g, b
    
    # Normalize to 0-1 range
    r_norm, g_norm, b_norm = r/255.0, g/255.0, b/255.0
    
    # Calculate luminance (perceived brightness)
    luminance = 0.299 * r_norm + 0.587 * g_norm + 0.114 * b_norm
    
    # Original blue ratio calculation
    total = r_norm + g_norm + b_norm + 0.000001
    blue_ratio = b_norm / total
    shrunk_ratio = blue_ratio * 1.5  # 1.5 to shorten the curve

    reduction_factor = 1.0

    # Additional reduction for dark pixels
    if dark_strength > 0 and luminance < luminance_threshold:
        # More blue reduction in darker areas
        darkness_factor = 1 - (luminance / luminance_threshold)
        additional_reduction = 1 - (dark_strength * darkness_factor * 0.1)  # Scale down the effect
        reduction_factor *= additional_reduction

    # Original blue reduction based on dominance
    if strength > 0:
        # Same formula as in the shell script
        pi = math.pi
        exp_term = math.exp(3 * shrunk_ratio)
        sin_term = math.sin(2 * pi * shrunk_ratio)
        cos_term = math.cos(2 * pi * shrunk_ratio)
        exp_denom = math.exp(3)

        result = ((1/4) * (-4*pi**2*exp_term + 6*pi*sin_term - 9*cos_term + 9 + 4*pi**2) *
                 math.exp(3 - 3*shrunk_ratio) / (pi**2 * (1 - exp_denom)) - 1) * strength + 1
        reduction_factor *= result
    
    # Apply reduction and clamp
    new_b = max(0, min(255, b_norm * reduction_factor * 255))
    
    return r, g, int(new_b)

def apply_blue_reduction(image, strength, dark_strength=0):
    """Apply blue reduction to the entire image."""
    if strength == 0 and dark_strength == 0:
        return image
    
    # Convert to RGB if not already
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Convert to numpy array for faster processing
    img_array = np.array(image)
    
    # Apply blue reduction pixel by pixel
    for y in range(img_array.shape[0]):
        for x in range(img_array.shape[1]):
            r, g, b = img_array[y, x]
            new_r, new_g, new_b = reduce_blue_in_pixel(r, g, b, strength, dark_strength)
            img_array[y, x] = [new_r, new_g, new_b]
    
    return Image.fromarray(img_array)

def apply_adjustments(image, saturation=100, black_level=0, contrast=1, shadows=0):
    """Apply various image adjustments."""
    
    # Saturation
    if saturation != 100:
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(saturation / 100.0)
    
    # Black level adjustment (similar to +level in ImageMagick)
    if black_level > 0:
        # This raises the black point
        img_array = np.array(image)
        img_array = np.clip(img_array + (black_level * 255 / 100), 0, 255).astype(np.uint8)
        image = Image.fromarray(img_array)
    
    # Contrast adjustment (simplified version of sigmoidal contrast)
    if contrast != 0:
        if contrast > 0:
            # Increase contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1 + contrast * 0.2)
        else:
            # Decrease contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1 + contrast * 0.1)
    
    # Shadow brightening (simplified)
    if shadows > 0:
        img_array = np.array(image).astype(float)
        # Brighten darker areas more than lighter areas
        luminance = 0.299 * img_array[:,:,0] + 0.587 * img_array[:,:,1] + 0.114 * img_array[:,:,2]
        shadow_mask = (255 - luminance) / 255  # Invert so dark areas have higher values
        
        for channel in range(3):
            adjustment = shadow_mask * shadows * 5  # Scale the effect
            img_array[:,:,channel] = np.clip(img_array[:,:,channel] + adjustment, 0, 255)
        
        image = Image.fromarray(img_array.astype(np.uint8))
    
    return image

def crop_to_ratio(image, ratio_str):
    """Crop image to specified ratio."""
    width, height = image.size
    ratio_parts = ratio_str.split(':')
    target_ratio = float(ratio_parts[0]) / float(ratio_parts[1])
    
    current_ratio = width / height
    
    if current_ratio > target_ratio:
        # Too wide, crop width
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        image = image.crop((left, 0, left + new_width, height))
    else:
        # Too tall, crop height
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        image = image.crop((0, top, width, top + new_height))
    
    return image

def simple_dither(image, palette_path, method='floyd'):
    """Apply dithering using PIL's built-in methods."""
    # Load the palette
    palette_img = Image.open(palette_path)
    
    # Convert image to P mode with the palette
    if method.lower() == 'none':
        # No dithering
        quantized = image.quantize(palette=palette_img, dither=Image.NONE)
    else:
        # Floyd-Steinberg dithering (PIL's default and most similar to ImageMagick)
        quantized = image.quantize(palette=palette_img, dither=Image.FLOYDSTEINBERG)
    
    # Convert back to RGB
    return quantized.convert('RGB')

def main():
    parser = argparse.ArgumentParser(description='Process images for 7-color e-ink display')
    parser.add_argument('image_path', help='Path to input image')
    parser.add_argument('--diffusion', type=int, default=85, help='Dither diffusion amount (not used in PIL version)')
    parser.add_argument('--blue-reduction', type=float, default=0, help='Blue reduction strength')
    parser.add_argument('--dark-blue-reduction', type=float, default=0, help='Additional blue reduction for dark pixels')
    parser.add_argument('--saturation', type=int, default=100, help='Saturation percentage')
    parser.add_argument('--black-level', type=int, default=0, help='Black level percentage')
    parser.add_argument('--contrast', type=float, default=1, help='Contrast adjustment')
    parser.add_argument('--shadows', type=float, default=0, help='Shadow brightening strength')
    parser.add_argument('--dither-method', default='FloydSteinberg', choices=['FloydSteinberg', 'None'], 
                       help='Dither method')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image_path):
        print(f"Error: Image file '{args.image_path}' not found.")
        sys.exit(1)
    
    # Create output directory
    os.makedirs('converted', exist_ok=True)
    
    # Generate output path
    base_name = os.path.splitext(os.path.basename(args.image_path))[0]
    output_path = os.path.join('converted', f'{base_name}_converted.bmp')
    
    print(f"Processing '{args.image_path}' -> '{output_path}'")
    print(f"Settings: Blue Reduction: {args.blue_reduction}, Dark Blue Reduction: {args.dark_blue_reduction}, "
          f"Saturation: {args.saturation}%, Black Level: {args.black_level}%, "
          f"Contrast: {args.contrast}, Shadows: {args.shadows}")
    
    # Load image
    image = Image.open(args.image_path)
    print(f"Original dimensions: {image.size}")
    
    # Determine orientation and crop
    width, height = image.size
    if width > height:
        # Landscape
        crop_ratio = "5:3"
        final_dimensions = (800, 480)
        orientation = "landscape"
    else:
        # Portrait
        crop_ratio = "3:5"
        final_dimensions = (480, 800)
        orientation = "portrait"
    
    print(f"Detected {orientation} orientation, cropping to {crop_ratio} and scaling to {final_dimensions}")
    
    # Process image
    image = crop_to_ratio(image, crop_ratio)
    image = image.resize(final_dimensions, Image.LANCZOS)
    
    # Apply blue reduction
    image = apply_blue_reduction(image, args.blue_reduction, args.dark_blue_reduction)
    
    # Apply other adjustments
    image = apply_adjustments(image, args.saturation, args.black_level, args.contrast, args.shadows)
    
    # Check if palette exists
    palette_path = 'palette_7color.gif'
    if os.path.exists(palette_path):
        # Apply dithering
        image = simple_dither(image, palette_path, args.dither_method)
    else:
        print(f"Warning: Palette file '{palette_path}' not found. Skipping dithering.")
    
    # Save result
    image.save(output_path, 'BMP')
    print("Done.")

if __name__ == '__main__':
    main()
