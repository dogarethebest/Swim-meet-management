import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H

def generate_qr_code(data: str, save_path: str):
    # Create QR code object
    qr = qrcode.QRCode(
        version=15,
        error_correction=ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    # Add data and make the QR code
    qr.add_data(data)
    qr.make(fit=True)

    # Generate the image
    img = qr.make_image(fill_color="black", back_color="white")

    # Save to file
    img.save(save_path)
    print(f"QR code saved to: {save_path}")



x = input("Will the meat be created by hand(H) or automated(A)?").upper

if (x=="H"):
    print("H")