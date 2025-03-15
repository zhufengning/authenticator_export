import sqlite3
import argparse
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
import re

def sanitize_filename(filename):
    """Replace invalid characters in filenames with underscore"""
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def create_qr_with_labels(name, username, oath_secret_key, output_path):
    """Create QR code with site name and username labels at the top"""
    # Format the otpauth URI
    otpauth_uri = f"otpauth://totp/{username}?secret={oath_secret_key}&issuer={name}"
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(otpauth_uri)
    qr.make(fit=True)
    
    # Create QR code image and convert it to PIL Image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.get_image()  # Convert to a standard PIL Image
    qr_width, qr_height = qr_img.size
    
    # Create a new image with extra space for labels
    label_height = 60  # Space for labels
    img = Image.new('RGB', (qr_width, qr_height + label_height), 'white')
    
    # Add QR code to the new image
    img.paste(qr_img, (0, label_height))
    
    # Add site name and username as text
    draw = ImageDraw.Draw(img)
    
    # Try to use Arial font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        font = ImageFont.load_default()
    
    # Add site name (top left)
    draw.text((10, 10), f"Site: {name}", fill='black', font=font)
    
    # Add username (top left, below site name)
    draw.text((10, 35), f"User: {username}", fill='black', font=font)
    
    # Create sanitized filename
    safe_name = sanitize_filename(name)
    safe_username = sanitize_filename(username)
    filename = f"{safe_name}_{safe_username}.png"
    
    # Save the image
    output_file = os.path.join(output_path, filename)
    img.save(output_file)
    print(f"Created QR code: {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Export 2FA accounts to QR code images')
    parser.add_argument('db_path', help='Path to SQLite database file')
    parser.add_argument('output_path', help='Path to output directory for QR code images')
    args = parser.parse_args()
    
    # Ensure output directory exists
    if not os.path.exists(args.output_path):
        os.makedirs(args.output_path)
    
    # Connect to the database
    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Query the accounts table
    cursor.execute("SELECT name, username, oath_secret_key FROM accounts")
    accounts = cursor.fetchall()
    
    if not accounts:
        print("No accounts found in the database.")
        return
    
    print(f"Found {len(accounts)} accounts. Generating QR codes...")
    
    # Generate QR codes for each account
    for account in accounts:
        name = account['name']
        username = account['username']
        oath_secret_key = account['oath_secret_key']
        
        create_qr_with_labels(name, username, oath_secret_key, args.output_path)
    
    print(f"QR code generation complete. Images saved to {args.output_path}")
    conn.close()

if __name__ == "__main__":
    main()