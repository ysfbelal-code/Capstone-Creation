from groq_api import generate_response
from huggingface_hub import InferenceClient
import requests, config

class ImageGenerator:
    def __init__(self) -> None:
        self.MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
        self.FILTER_API_URL = "https://filters-zeta.vercel.app/api/filter"

        self.ENHANCE_SYS = (
            "Improve prompts for text-to-image. Return ONLY the enhanced prompt. "
            "Add subject, style, lighting, camera angle, background, colors. Keep it safe."
        )

        # This is only for image quality guidance, not safety filtering
        self.NEGATIVE = "low quality, blurry, distorted, watermark, text, cropped"

        self.img_client = InferenceClient(provider="hf-inference", api_key=config.HF_API_KEY)
    
    def check_prompt_with_filter(self, prompt: str):
        try:
            response = requests.post(
                self.FILTER_API_URL, 
                json={'prompt': prompt}, 
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict):
                return {'ok': False, 'reason':'Invalid filter API response'}

            return data

        except Exception as e:
            return {
                'ok': False, 
                'reason': f'Filter API error: {str(e)}'
            }
        
    def enhance(self, raw: str):
        out = generate_response(
        f"{self.ENHANCE_SYS}\nUser prompt: {raw}", 
        temperature=0.4, 
        max_tokens=220
        )
        return (out or raw).strip()
    
    def gen_image(self, prompt: str):
        filter_result = self.check_prompt_with_filter_api(prompt)
        if not filter_result.get('ok'):
            return None, f"Prompt blocked by safety filter. {filter_result.get('reason', 'Unsafe prompt')}"

        try:
            return self.img_client.text_to_image(
                prompt=prompt, 
                negative_prompt=self.NEGATIVE, 
                model=self.MODEL_ID
            ), None
        except Exception as e:
            msg = str(e)

            if "negative_prompt" in msg or "unexpected keyword" in msg:
                try:
                    return self.img_client.text_to_image(
                prompt=prompt,  
                model=self.MODEL_ID
            ), None
                except Exception as e2:
                    msg = str(e2)
            
            if any(x in msg for x in ["402", "Payment required", "pre-paid credits"]):
                return None, f"Image backend requires credits or model not available on hf-inference.\n\nRaw error: {msg}"
            
            if "404" in msg or "Not Found" in msg:
                return None, f"Model not served on this provider route (hf-inference).\n\nRaw error: {msg}"

            return None, f"Error during image generation: {msg}"