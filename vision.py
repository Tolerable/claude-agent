"""
VISION.PY - Camera capture and image description
================================================
Gives Claude the ability to see through cameras.

Usage:
    from vision import capture_frame, describe_image
    frame, path = capture_frame(camera_index=0)
    description = describe_image(path)
"""
import sys
import io
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
SNAPSHOTS_DIR = BASE_DIR / "snapshots"
SNAPSHOTS_DIR.mkdir(exist_ok=True)

# Load config
try:
    from config import CAMERA_INDEX, OLLAMA_MODEL
except ImportError:
    CAMERA_INDEX = 0
    OLLAMA_MODEL = "llava:7b"


def capture_frame(camera_index=None, save=True):
    """
    Capture a frame from camera.
    Returns: (frame, filepath) or (None, error_message)
    """
    camera_index = camera_index if camera_index is not None else CAMERA_INDEX

    try:
        import cv2
    except ImportError:
        return None, "OpenCV not installed. Run: pip install opencv-python"

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return None, f"Could not open camera {camera_index}"

    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None, "Failed to capture frame"

    filepath = None
    if save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = SNAPSHOTS_DIR / f"snap_{timestamp}.jpg"
        cv2.imwrite(str(filepath), frame)

    return frame, str(filepath) if filepath else None


def describe_image(image_path, prompt=None):
    """
    Use vision LLM to describe an image.
    Requires Ollama with llava model.
    """
    import base64
    import requests

    prompt = prompt or "Describe what you see in this image briefly."

    # Read and encode image
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
    except Exception as e:
        return f"Error reading image: {e}"

    # Use Ollama with vision model
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llava:7b",
                "prompt": prompt,
                "images": [image_data],
                "stream": False
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("response", "No description generated")
        return f"Ollama error: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "Ollama not running. Start with: ollama serve"
    except Exception as e:
        return f"Error: {e}"


def list_cameras(max_check=5):
    """List available cameras."""
    try:
        import cv2
    except ImportError:
        return ["OpenCV not installed"]

    cameras = []
    for i in range(max_check):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cameras.append(f"Camera {i}: available")
            cap.release()

    return cameras if cameras else ["No cameras found"]


def screenshot():
    """Take a screenshot instead of camera capture."""
    try:
        from PIL import ImageGrab
    except ImportError:
        return None, "Pillow not installed. Run: pip install Pillow"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = SNAPSHOTS_DIR / f"screen_{timestamp}.png"

    screenshot = ImageGrab.grab()
    screenshot.save(filepath)

    return screenshot, str(filepath)


if __name__ == "__main__":
    print("Available cameras:")
    for cam in list_cameras():
        print(f"  {cam}")

    print("\nTesting capture...")
    frame, path = capture_frame()
    if frame is not None:
        print(f"Captured: {path}")
        print("\nDescribing image...")
        desc = describe_image(path)
        print(f"Description: {desc}")
    else:
        print(f"Error: {path}")
