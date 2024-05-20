import cv2
import numpy as np

def calculate_mse(original, modified):
    # Calculate Mean Squared Error (MSE)
    mse = np.mean((original - modified) ** 2)
    return mse

def calculate_psnr(original, modified):
    # Calculate the maximum pixel value of the image
    max_pixel_value = 255.0
    
    # Calculate Mean Squared Error (MSE)
    mse = calculate_mse(original, modified)
    
    if mse == 0:  # MSE is zero means no noise is present in the signal
                  # Therefore PSNR have no importance
        return float('inf')
    
    # Calculate PSNR
    psnr = 20 * np.log10(max_pixel_value / np.sqrt(mse))
    return psnr

def main():
    # Read the original image
    original_path = input("Enter the path of the original image: ")
    original_image = cv2.imread(original_path, cv2.IMREAD_GRAYSCALE)
    
    # Read the modified image
    modified_path = input("Enter the path of the modified image: ")
    modified_image = cv2.imread(modified_path, cv2.IMREAD_GRAYSCALE)
    
    # Check if images are loaded properly
    if original_image is None or modified_image is None:
        print("Error: Could not open or find the images!")
        return
    
    # Check if images have the same size
    if original_image.shape != modified_image.shape:
        print("Error: Images must have the same dimensions!")
        return
    
    # Calculate PSNR
    psnr_value = calculate_psnr(original_image, modified_image)
    print(f"PSNR value is {psnr_value} dB")

if __name__ == "__main__":
    main()
