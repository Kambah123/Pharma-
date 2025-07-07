import openai
import os
import json

def generate_brand_package(molecule, therapeutic_area, color_palette=None):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    # 1. Generate brand names, slogans, leaflet with GPT-4
    system_prompt = (
        "You are a pharmaceutical branding AI. "
        "Given a molecule, therapeutic area, and color palette, generate: "
        "- 3 creative brand names (list)\n"
        "- 1 English slogan (short, catchy)\n"
        "- Bengali translation of the slogan\n"
        "- A leaflet draft (JSON with sections: Introduction, Benefits, Clinical References, Patient Info (BN), Compliance)\n"
        "Respond in JSON with keys: brand_names, slogan_en, slogan_bn, leaflet_json."
    )
    user_prompt = f"Molecule: {molecule}\nTherapeutic Area: {therapeutic_area}\nColor Palette: {color_palette or ''}"
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.8,
        max_tokens=700
    )
    try:
        content = response.choices[0].message.content
        data = json.loads(content)
        brand_names = data.get("brand_names", [])
        slogan_en = data.get("slogan_en", "")
        slogan_bn = data.get("slogan_bn", "")
        leaflet_json = data.get("leaflet_json", {})
    except Exception:
        brand_names = ["BrandX", "BrandY", "BrandZ"]
        slogan_en = "Innovate Health."
        slogan_bn = "স্বাস্থ্য উদ্ভাবন করুন।"
        leaflet_json = {"sections": []}
    # 2. Generate logo concepts with DALL-E 3
    logo_concepts = []
    for name in brand_names:
        try:
            dalle_prompt = f"Pharmaceutical brand logo for '{name}', therapeutic area: {therapeutic_area}, color palette: {color_palette}. Minimal, modern, professional, high quality."
            dalle_resp = openai.Image.create(
                prompt=dalle_prompt,
                n=1,
                size="512x512",
                model="dall-e-3"
            )
            logo_url = dalle_resp['data'][0]['url']
        except Exception:
            logo_url = f"https://dummy.dalle.api/logo_{name.lower()}.png"
        logo_concepts.append({"url": logo_url})
    return {
        "brand_names": brand_names,
        "logo_concepts": logo_concepts,
        "slogans": [{"en": slogan_en, "bn": slogan_bn}],
        "color_palette": color_palette,
        "leaflet_json": leaflet_json
    }
