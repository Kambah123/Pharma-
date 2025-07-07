import openai
import os
import json

def generate_insights(molecule, therapeutic_area, benefits=None, prompt=None):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    system_prompt = (
        "You are a pharmaceutical brand strategist. "
        "Given a molecule, therapeutic area, and product benefits, generate: "
        "- Key competitors (list)\n"
        "- Brand positioning (1-2 lines)\n"
        "- Color palette (3-4 colors, each with name, hex, and reason)\n"
        "- Clinical trials (list, each with name and 1-line summary). "
        "Respond in JSON with keys: competitors, brand_positioning, color_palette, clinical_trials."
    )
    user_prompt = f"Molecule: {molecule}\nTherapeutic Area: {therapeutic_area}\nBenefits: {benefits or ''}\n{prompt or ''}"
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=600
    )
    try:
        content = response.choices[0].message.content
        data = json.loads(content)
        return data
    except Exception:
        return {"competitors": [], "brand_positioning": "", "color_palette": [], "clinical_trials": []}
