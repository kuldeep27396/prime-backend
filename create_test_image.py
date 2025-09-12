"""
Create a proper test image for vision API testing
"""

import base64
from PIL import Image, ImageDraw
import io


def create_test_image():
    """Create a simple test image that meets vision model requirements"""
    
    # Create a 100x100 pixel image with some content
    img = Image.new('RGB', (100, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple face-like pattern
    # Head circle
    draw.ellipse([20, 20, 80, 80], outline='black', width=2)
    
    # Eyes
    draw.ellipse([35, 35, 40, 40], fill='black')
    draw.ellipse([60, 35, 65, 40], fill='black')
    
    # Mouth
    draw.arc([40, 55, 60, 65], start=0, end=180, fill='black', width=2)
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return img_base64


if __name__ == "__main__":
    test_image = create_test_image()
    print(f"Created test image with {len(test_image)} characters")
    print(f"First 100 characters: {test_image[:100]}...")
    
    # Save to file for reuse
    with open('test_image_b64.txt', 'w') as f:
        f.write(test_image)
    
    print("Test image saved to test_image_b64.txt")