from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from ai.insights import generate_insights  # Placeholder
from ai.brand_package import generate_brand_package  # Placeholder
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProjectInput(BaseModel):
    product_name: Optional[str]
    molecule: str
    therapeutic_area: str
    benefits: Optional[str]
    prompt: Optional[str]

@app.post("/api/projects/create")
async def create_project(input: ProjectInput):
    # 1. Call Strategic Insights Engine (OpenAI, vector search, etc.)
    insights = generate_insights(
        molecule=input.molecule,
        therapeutic_area=input.therapeutic_area,
        benefits=input.benefits,
        prompt=input.prompt
    )
    # 2. Call Brand Package Generator (OpenAI, DALL-E, etc.)
    brand_package = generate_brand_package(
        molecule=input.molecule,
        therapeutic_area=input.therapeutic_area,
        color_palette=insights.get("color_palette")
    )
    # 3. Store project in Supabase
    user_id = "demo-user"  # TODO: Replace with real user ID from auth
    project_data = {
        "name": input.product_name,
        "molecule": input.molecule,
        "therapeutic_area": input.therapeutic_area,
        "benefits": input.benefits,
        "prompt": input.prompt,
        "user_id": user_id
    }
    res = supabase.table("projects").insert(project_data).execute()
    project_id = res.data[0]["id"] if res.data else None
    # 4. Store insights in Supabase
    insights_data = {
        "project_id": project_id,
        "user_id": user_id,
        "competitors": insights.get("competitors"),
        "brand_positioning": insights.get("brand_positioning"),
        "color_palette": insights.get("color_palette"),
        "clinical_trials": insights.get("clinical_trials"),
    }
    supabase.table("insights").insert(insights_data).execute()
    # 5. Store brand package in Supabase
    for idx, name in enumerate(brand_package.get("brand_names", [])):
        brand_element_data = {
            "project_id": project_id,
            "user_id": user_id,
            "brand_name": name,
            "logo_url": brand_package.get("logo_concepts", [{}])[idx].get("url") if idx < len(brand_package.get("logo_concepts", [])) else None,
            "slogan_en": brand_package.get("slogans", [{}])[0].get("en"),
            "slogan_bn": brand_package.get("slogans", [{}])[0].get("bn"),
            "color_palette": brand_package.get("color_palette"),
            "leaflet_json": brand_package.get("leaflet_json"),
            "compliance_status": "pending"
        }
        supabase.table("brand_elements").insert(brand_element_data).execute()
    # 6. Return structured response
    return {
        "project": {
            "id": project_id,
            **project_data
        },
        "insights": insights,
        "brand_package": brand_package
    }

# --- Iterative Editing & Compliance/Export Endpoints ---
from fastapi import Body

@app.patch("/api/projects/{project_id}/brand_name")
def update_brand_name(project_id: str, brand_name: str = Body(...)):
    res = supabase.table("brand_elements").update({"brand_name": brand_name}).eq("project_id", project_id).execute()
    if res.error:
        raise HTTPException(400, res.error.message)
    return {"success": True}

@app.patch("/api/projects/{project_id}/slogan")
def update_slogan(project_id: str, slogan: str = Body(...)):
    res = supabase.table("brand_elements").update({"slogan_en": slogan}).eq("project_id", project_id).execute()
    if res.error:
        raise HTTPException(400, res.error.message)
    return {"success": True}

@app.patch("/api/projects/{project_id}/leaflet")
def update_leaflet(project_id: str, leaflet: str = Body(...)):
    res = supabase.table("brand_elements").update({"leaflet_json": {"sections": [{"title": "Leaflet", "content": leaflet}]}}).eq("project_id", project_id).execute()
    if res.error:
        raise HTTPException(400, res.error.message)
    return {"success": True}

@app.post("/api/projects/{project_id}/compliance_check")
def compliance_check(project_id: str):
    import openai
    import os
    openai.api_key = os.getenv("OPENAI_API_KEY")
    # Fetch leaflet and brand info for this project
    brand_row = supabase.table("brand_elements").select("brand_name, slogan_en, slogan_bn, leaflet_json").eq("project_id", project_id).single().execute()
    if not brand_row.data:
        raise HTTPException(404, "Brand element not found")
    brand = brand_row.data
    leaflet = brand.get("leaflet_json", {})
    brand_name = brand.get("brand_name", "")
    slogan_en = brand.get("slogan_en", "")
    # Compose compliance prompt
    system_prompt = (
        "You are a pharmaceutical regulatory compliance expert for Bangladesh DGDA. "
        "Given the following brand name, slogan, and leaflet sections, check if the content is compliant with DGDA rules for pharmaceutical marketing. "
        "Respond ONLY with one word: 'approved' or 'rejected'."
    )
    user_prompt = f"Brand: {brand_name}\nSlogan: {slogan_en}\nLeaflet: {leaflet}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=10
        )
        result = response.choices[0].message.content.strip().lower()
        if "approved" in result:
            status = "approved"
        elif "rejected" in result:
            status = "rejected"
        else:
            status = "pending"
    except Exception:
        status = "pending"
    res = supabase.table("brand_elements").update({"compliance_status": status}).eq("project_id", project_id).execute()
    if res.error:
        raise HTTPException(400, res.error.message)
    return {"success": True, "status": status}

@app.get("/api/projects/{project_id}/export/pdf")
def export_leaflet_pdf(project_id: str):
    # Dummy: return a fake download URL
    return {"url": f"https://example.com/fake-leaflet-{project_id}.pdf"}

# --- End Iterative Editing & Compliance/Export ---

from fastapi import Request

@app.get("/api/projects/list")
def list_projects(request: Request):
    user_id = request.query_params.get("user_id")
    query = supabase.table("projects").select("*")
    if user_id:
        query = query.eq("user_id", user_id)
    res = query.execute()
    projects = res.data if res.data else []
    return {"projects": projects}

@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    res = supabase.table("projects").select("*").eq("id", project_id).execute()
    if not res.data:
        return {"error": "Project not found"}, 404
    project = res.data[0]
    # Fetch insights from Supabase
    insights_res = supabase.table("insights").select("*").eq("project_id", project_id).execute()
    insights = insights_res.data[0] if insights_res.data else {}
    # Fetch brand elements from Supabase
    brand_elements_res = supabase.table("brand_elements").select("*").eq("project_id", project_id).execute()
    brand_elements = brand_elements_res.data if brand_elements_res.data else []
    # Compose brand_package from brand_elements
    brand_package = {
        "brand_names": [be["brand_name"] for be in brand_elements],
        "logo_concepts": [{"url": be["logo_url"]} for be in brand_elements],
        "slogans": [{"en": be["slogan_en"], "bn": be["slogan_bn"]} for be in brand_elements],
        "color_palette": brand_elements[0]["color_palette"] if brand_elements else None,
        "leaflet_json": brand_elements[0]["leaflet_json"] if brand_elements else None,
        "compliance_status": brand_elements[0]["compliance_status"] if brand_elements else None
    } if brand_elements else {}
    return {
        "project": project,
        "insights": insights,
        "brand_package": brand_package
    }
