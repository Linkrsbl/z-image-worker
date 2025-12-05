import base64
import io
import os

import runpod
import torch
from diffusers import ZImagePipeline

# -------------------------
#  모델 로딩 (컨테이너 시작 시 1번)
# -------------------------

MODEL_ID = os.getenv("MODEL_ID", "Tongyi-MAI/Z-Image-Turbo")

device = "cuda" if torch.cuda.is_available() else "cpu"

# GPU면 bfloat16, 아니면 float32
if device == "cuda":
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
else:
    dtype = torch.float32

print(f"[z-image-worker] loading model: {MODEL_ID}")
print(f"[z-image-worker] device: {device}, dtype: {dtype}")

pipe = ZImagePipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=dtype,
    # 필요시 옵션 추가
    low_cpu_mem_usage=False,
)

pipe.to(device)


# -------------------------
#  이미지 생성 함수
# -------------------------
def generate_image(event):
    """
    RunPod 서버리스 이벤트에서 prompt 등을 읽어서
    base64 PNG 이미지로 반환.
    """
    body = event.get("input", {}) or {}

    prompt = body.get(
        "prompt",
        "a high quality studio photo of a white pomeranian dog wearing sunglasses, 4k, soft lighting",
    )
    negative_prompt = body.get("negative_prompt", None)
    steps = int(body.get("num_inference_steps", 6))
    guidance_scale = float(body.get("guidance_scale", 0.0))
    seed = body.get("seed", None)

    height = int(body.get("height", 1024))
    width = int(body.get("width", 1024))

    generator = None
    if seed is not None:
        generator = torch.Generator(device=device).manual_seed(int(seed))

    print("[z-image-worker] generating image...")
    print(f" prompt={prompt!r}")
    print(f" steps={steps}, guidance_scale={guidance_scale}, seed={seed}")

    with torch.inference_mode():
        out = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            height=height,
            width=width,
            generator=generator,
        )

    image = out.images[0]

    # PNG → base64 인코딩
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode("utf-8")

    return {
        "image_base64": b64,
        "seed": seed,
        "height": height,
        "width": width,
    }


# -------------------------
#  RunPod handler
# -------------------------
def handler(event):
    """
    RunPod 서버리스에서 호출되는 엔트리 포인트
    """
    try:
        return generate_image(event)
    except Exception as e:  # noqa: BLE001
        # 에러도 응답으로 돌려주면 디버깅하기 편함
        return {"error": str(e)}


# RunPod 서버리스 시작
runpod.serverless.start({"handler": handler})
