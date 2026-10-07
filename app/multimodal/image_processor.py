import base64
import io
from pathlib import Path
from typing import Any, Dict, Optional
from PIL import Image, ImageStat
from app.utils.logging import get_logger

logger = get_logger("image_processor")

class ImageProcessor:
    """Processes images (PNG, JPG, JPEG, WEBP), extracts visual metrics, and prepares base64 encoding."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

    def extract(self) -> Dict[str, Any]:
        if not self.file_path.exists():
            raise FileNotFoundError(f"Image file not found: {self.file_path}")

        with Image.open(self.file_path) as img:
            width, height = img.size
            format_name = img.format
            mode = img.mode

            # Compute image statistics (brightness, contrast)
            stat = ImageStat.Stat(img.convert("L"))
            mean_brightness = stat.mean[0] if stat.mean else 0
            std_contrast = stat.stddev[0] if stat.stddev else 0

            # Base64 string for Vision LLM calls
            b64_str = self.to_base64()

            # OCR Extraction check
            ocr_text = self._attempt_ocr(img)

            aspect_ratio = round(width / max(height, 1), 2)
            orientation = "landscape" if width > height else ("portrait" if height > width else "square")

            summary_text = (
                f"Image: {self.file_path.name}\n"
                f"Dimensions: {width}x{height} ({orientation}, aspect ratio: {aspect_ratio})\n"
                f"Format: {format_name}, Color Mode: {mode}\n"
                f"Average Luminance: {mean_brightness:.1f}/255, Contrast STD: {std_contrast:.1f}\n"
            )
            if ocr_text:
                summary_text += f"\nExtracted OCR Text:\n{ocr_text}"
            else:
                summary_text += "\nVisual Type: Visual asset/diagram/chart. Ready for multimodal Vision Agent analysis."

            return {
                "metadata": {
                    "filename": self.file_path.name,
                    "file_size": self.file_path.stat().st_size,
                    "width": width,
                    "height": height,
                    "format": format_name,
                    "mode": mode,
                    "aspect_ratio": aspect_ratio,
                    "orientation": orientation,
                    "mean_brightness": round(mean_brightness, 2),
                    "std_contrast": round(std_contrast, 2),
                },
                "ocr_text": ocr_text,
                "base64_data": b64_str,
                "full_text": summary_text,
            }

    def to_base64(self) -> str:
        """Converts image to data URL / base64 string."""
        with open(self.file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        ext = self.file_path.suffix.lower().replace(".", "")
        mime = f"image/{ext}" if ext != "jpg" else "image/jpeg"
        return f"data:{mime};base64,{encoded}"

    def _attempt_ocr(self, img: Image.Image) -> Optional[str]:
        """Tries to extract OCR text if pytesseract is installed; fails gracefully otherwise."""
        try:
            import pytesseract
            text = pytesseract.image_to_string(img)
            return text.strip() if text else None
        except Exception:
            return None
