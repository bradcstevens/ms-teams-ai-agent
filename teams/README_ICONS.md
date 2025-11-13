# Teams App Icons

## Required Icons

### color.png
- Size: 192x192 pixels
- Format: PNG
- Background: Solid color (#0078D4 recommended)
- Content: App logo/icon

### outline.png
- Size: 32x32 pixels
- Format: PNG with transparency
- Background: Transparent
- Content: Monochrome outline version of logo

## Creating Icons

Use any image editing tool to create the icons. Recommended tools:
- Adobe Photoshop
- GIMP (free)
- Figma (free)
- Canva (free)

## Placeholder Icons

Run the following Python script to create placeholder icons:

```python
from PIL import Image, ImageDraw, ImageFont

# Color icon (192x192)
color = Image.new('RGB', (192, 192), '#0078D4')
# Add your design here
color.save('color.png')

# Outline icon (32x32)
outline = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
# Add your design here
outline.save('outline.png')
```
