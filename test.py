from diffusers import StableDiffusionPipeline
import torch

# 🧠 Ton texte (prompt)
prompt = "a futuristic Moroccan city at sunset with neon lights"

# ✨ Charge le modèle Stable Diffusion (local, pas besoin d'internet après)
print("⏳ Chargement du modèle (première utilisation: 3-5 minutes)...")
model_id = "runwayml/stable-diffusion-v1-5"

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"📍 Utilisation du: {device}")

pipe = StableDiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float32,
    safety_checker=None  # Désactive le vérificateur de contenu
)
pipe = pipe.to(device)

# 🚀 Génère l'image
print("🎨 Génération de l'image...")
image = pipe(prompt, num_inference_steps=50).images[0]

# 📸 Sauvegarde l'image
image.save("output.png")

print("✅ Image générée avec succès : output.png")