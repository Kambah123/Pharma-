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

# Updated Pydantic model to match frontend and Supabase schema
class CreateProjectRequest(BaseModel):
    project_name: Optional[str] = None
    molecule_names: Optional[str] = None
    therapeutic_area: Optional[str] = None
    key_differentiating_benefits: Optional[str] = None
    natural_language_prompt: Optional[str] = None

class ProjectResponse(BaseModel): # Define a response model for clarity
    id: str # UUID will be string
    user_id: str
    project_name: Optional[str] = None
    molecule_names: Optional[str] = None
    therapeutic_area: Optional[str] = None
    key_differentiating_benefits: Optional[str] = None
    # Add other fields as necessary, e.g., status, created_at
    # For now, keeping it simple to reflect the created project's core data

@app.post("/api/projects/create", response_model=ProjectResponse) # Added response_model
async def create_project(payload: CreateProjectRequest):
    # TODO: Extract user_id from authenticated session/token
    user_id = "demo-user-fixme" # IMPORTANT: Replace with real user ID from auth

    # Log received payload for debugging
    print(f"Received project creation request: {payload}")

    # --- 1. Data Extraction (if natural language prompt is primary) ---
    # If natural_language_prompt is provided and other fields are sparse,
    # an NLP model (e.g., GPT) could parse it to fill in:
    # payload.molecule_names, payload.therapeutic_area, payload.key_differentiating_benefits
    # For now, we'll assume these are either provided or the AI modules can handle missing info.
    # Example (conceptual):
    # if payload.natural_language_prompt and not (payload.molecule_names and payload.therapeutic_area):
    #     extracted_data = parse_prompt_with_llm(payload.natural_language_prompt)
    #     payload.molecule_names = payload.molecule_names or extracted_data.get("molecule_names")
    #     payload.therapeutic_area = payload.therapeutic_area or extracted_data.get("therapeutic_area")
    #     # ... and so on

    if not payload.molecule_names or not payload.therapeutic_area:
        if payload.natural_language_prompt:
            # TODO: Implement LLM-based extraction if core fields are missing
            # For now, we'll pass along what we have to the AI modules.
            # Or, return an error if essential info for AI modules is truly missing and not in prompt.
            print("Warning: Core fields (molecule_names, therapeutic_area) missing, relying on prompt for AI modules.")
        else:
            raise HTTPException(status_code=400, detail="Molecule names and Therapeutic Area are required if not using a natural language prompt.")

    # --- 2. Call Strategic Insights Engine ---
    # Placeholder: Assumes generate_insights can handle potentially None inputs
    try:
        print(f"Calling generate_insights with: molecule='{payload.molecule_names}', therapeutic_area='{payload.therapeutic_area}', benefits='{payload.key_differentiating_benefits}', prompt='{payload.natural_language_prompt}'")
        insights = await generate_insights( # Assuming async if it involves I/O
            molecule=payload.molecule_names, # Corrected parameter name
            therapeutic_area=payload.therapeutic_area,
            benefits=payload.key_differentiating_benefits, # Corrected parameter name
            prompt=payload.natural_language_prompt # Pass prompt
        )
        # insights structure expected:
        # {
        #   "competitors": ["CompA", "CompB"],
        #   "brand_positioning": "Focus on X",
        #   "color_palette": {"primary": "#FFFFFF", "secondary": "#000000", "reasoning": "..."},
        #   "cited_trials": ["TrialX", "TrialY"]
        # }
    except Exception as e:
        print(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate strategic insights: {e}")

    # --- 3. Call Brand Package Generator ---
    # Placeholder: Assumes generate_brand_package can handle potentially None inputs
    try:
        print(f"Calling generate_brand_package with: molecule='{payload.molecule_names}', therapeutic_area='{payload.therapeutic_area}', color_palette='{insights.get('color_palette')}'")
        brand_package = await generate_brand_package( # Assuming async
            molecule=payload.molecule_names, # Corrected parameter name
            therapeutic_area=payload.therapeutic_area,
            # key_differentiating_benefits is not a direct input for generate_brand_package
            # natural_language_prompt is not a direct input for generate_brand_package
            # recommended_positioning is not a direct input for generate_brand_package in insights.py (it's used in the prompt construction)
            color_palette=insights.get("color_palette")
        )
        # brand_package structure from ai/brand_package.py:
        # {
        #   "brand_names": ["BrandA", "BrandB"], (List of strings)
        #   "logo_concepts": [{"url": "dalle_concept1_url"}], (List of dicts)
        #   "slogans": [{"english": "Slogan EN", "bengali": "স্লোগান বাংলা"}], (List of dicts)
        #   "color_palette": color_palette, (Passed through)
        #   "leaflet_json": { ... } (Dict)
        # }
    except Exception as e:
        print(f"Error generating brand package: {e}")
        #   "brand_name_suggestions": [{"name": "BrandA"}, {"name": "BrandB"}],
        #   "logo_concepts": [{"name": "Logo1", "prompt": "...", "image_url_placeholder": "dalle_concept1_url"}],
        #   "slogans": [{"english": "Slogan EN", "bengali": "স্লোগান বাংলা"}],
        #   "leaflet_draft": {"layout_json": { ... }}
        # }
    except Exception as e:
        print(f"Error generating brand package: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate brand package: {e}")

    # --- 4. Store project and generated elements in Supabase ---
    project_id = None
    try:
        # Create the main project entry
        project_insert_data = {
            "user_id": user_id,
            "project_name": payload.project_name,
            "molecule_names": payload.molecule_names,
            "therapeutic_area": payload.therapeutic_area,
            "key_differentiating_benefits": payload.key_differentiating_benefits,
            # "status": "draft" # Default status from schema
        }
        project_res = supabase.table("projects").insert(project_insert_data).execute()

        if not project_res.data:
            print(f"Supabase project insert error: {project_res.error}")
            raise HTTPException(status_code=500, detail="Failed to create project record in database.")

        created_project = project_res.data[0]
        project_id = created_project["id"]

        # Store brand elements (names, logos, slogans, leaflet, insights)
        elements_to_insert = []

        # Insights as brand elements
        if insights.get("competitors"):
            elements_to_insert.append({
                "project_id": project_id, "element_type": "insight_competitors",
                "content": {"competitors": insights["competitors"]}
            })
        if insights.get("brand_positioning"):
            elements_to_insert.append({
                "project_id": project_id, "element_type": "insight_brand_positioning",
                "content": {"positioning": insights["brand_positioning"]}
            })
        if insights.get("color_palette"):
            elements_to_insert.append({
                "project_id": project_id, "element_type": "insight_color_palette",
                "content": insights["color_palette"] # e.g. {"primary": "#...", "reasoning": "..."}
            })
        if insights.get("cited_trials"):
            elements_to_insert.append({
                "project_id": project_id, "element_type": "insight_cited_trials",
                "content": {"trials": insights["cited_trials"]}
            })

        # Brand package elements
        # Adjusted to match actual output of generate_brand_package
        for name_str in brand_package.get("brand_names", []): # brand_names is list of strings
            elements_to_insert.append({
                "project_id": project_id, "element_type": "brand_name_suggestion",
                "content": {"name": name_str} # Store as a dict in content
            })
        for logo_url_dict in brand_package.get("logo_concepts", []): # logo_concepts is list of {"url": "..."}
            elements_to_insert.append({
                "project_id": project_id, "element_type": "logo_concept",
                "content": logo_url_dict # Store {"url": "..."}
            })
        # Slogans structure: brand_package.get("slogans") is expected to be [{"english": "...", "bengali": "..."}]
        # The generate_brand_package returns: "slogans": [{"en": slogan_en, "bn": slogan_bn}]
        # This matches the iteration logic.
        for slogan_pair in brand_package.get("slogans", []): # slogans is list of dicts {"en": ..., "bn": ...}
            elements_to_insert.append({
                "project_id": project_id, "element_type": "slogan_suggestion",
                "content": slogan_pair
            })
        if brand_package.get("leaflet_json"): # Corrected key from "leaflet_draft" to "leaflet_json"
            elements_to_insert.append({
                "project_id": project_id, "element_type": "leaflet_draft", # Keep element_type as "leaflet_draft" for consistency
                "content": brand_package["leaflet_json"] # e.g. {"layout_json": {...}} or the direct JSON content
            })

        if elements_to_insert:
            elements_res = supabase.table("brand_elements").insert(elements_to_insert).execute()
            if elements_res.error:
                # TODO: Consider cleanup or marking project as incomplete if this fails
                print(f"Supabase brand_elements insert error: {elements_res.error}")
                raise HTTPException(status_code=500, detail="Failed to store generated brand elements.")

        # Prepare and return the main project data as per ProjectResponse model
        return ProjectResponse(
            id=str(project_id), # Ensure UUID is string
            user_id=user_id,
            project_name=created_project.get("project_name"),
            molecule_names=created_project.get("molecule_names"),
            therapeutic_area=created_project.get("therapeutic_area"),
            key_differentiating_benefits=created_project.get("key_differentiating_benefits")
        )

    except HTTPException as he:
        raise he # Re-raise HTTPExceptions
    except Exception as e:
        # TODO: If project_id was created but subsequent steps failed,
        # consider deleting the project or marking it as failed.
        print(f"An unexpected error occurred during project creation: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


# --- Iterative Editing & Compliance/Export Endpoints ---
# Note: The existing iterative editing and other endpoints below this point
# will need to be reviewed and updated to align with the new brand_elements structure.
# For example, updating a brand name might now mean updating a specific 'brand_name_suggestion'
# element in the 'brand_elements' table and marking it as 'is_selected = true'.
# This is outside the scope of the current step but important for future work.
# The Supabase table "insights" and the way "brand_elements" was previously structured
# (specific columns like brand_name, logo_url) are different from the new schema.
# These endpoints (update_brand_name, update_slogan, etc.) will need significant rework.
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
async def get_project(project_id: str): # Changed to async to potentially use async supabase client later if needed
    # Fetch the main project details
    project_res = supabase.table("projects").select("*").eq("id", project_id).single().execute()

    if not project_res.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = project_res.data

    # Fetch all associated brand elements for the project
    brand_elements_res = supabase.table("brand_elements").select("*").eq("project_id", project_id).execute()
    if brand_elements_res.error:
        # Log error and potentially raise HTTPException
        print(f"Error fetching brand elements for project {project_id}: {brand_elements_res.error}")
        raise HTTPException(status_code=500, detail="Could not fetch brand elements.")

    elements = brand_elements_res.data if brand_elements_res.data else []

    # Reconstruct insights and brand_package from elements
    insights_data = {
        "competitors": [],
        "brand_positioning": None,
        "color_palette": None, # This will take the content of the first found color palette insight
        "cited_trials": []
    }
    brand_package_data = {
        "brand_name_suggestions": [], # Will be list of {"name": "BrandA"}
        "logo_concepts": [], # Will be list of {"url": "..."} or {"name": "...", "prompt": "...", "image_url_placeholder": "..."}
        "slogans": [], # Will be list of {"english": "...", "bengali": "..."}
        "leaflet_draft": None, # Will be the content of leaflet_draft, e.g. {"layout_json": {...}}
        # Compliance status might be part of leaflet_draft or a separate element. For now, assume not directly here unless made an element.
    }

    for el in elements:
        element_type = el.get("element_type")
        content = el.get("content", {})
        if not content: # Ensure content is a dict if None or empty
            content = {}

        if element_type == "insight_competitors":
            insights_data["competitors"].extend(content.get("competitors", []))
        elif element_type == "insight_brand_positioning":
            if insights_data["brand_positioning"] is None: # Take the first one if multiple (though unlikely)
                insights_data["brand_positioning"] = content.get("positioning")
        elif element_type == "insight_color_palette":
            if insights_data["color_palette"] is None: # Take the first one
                insights_data["color_palette"] = content # content is the palette itself e.g. {"primary": "#...", "reasoning":"..."} or list from old insight
        elif element_type == "insight_cited_trials":
            insights_data["cited_trials"].extend(content.get("trials", []))

        elif element_type == "brand_name_suggestion":
            # content is expected to be {"name": "BrandName"}
            if content.get("name"):
                brand_package_data["brand_name_suggestions"].append(content)
        elif element_type == "logo_concept":
            # content is expected to be {"url": "..."} or similar
            brand_package_data["logo_concepts"].append(content)
        elif element_type == "slogan_suggestion":
            # content is expected to be {"english": "...", "bengali": "..."}
            brand_package_data["slogans"].append(content)
        elif element_type == "leaflet_draft":
            if brand_package_data["leaflet_draft"] is None: # Take the first one
                brand_package_data["leaflet_draft"] = content # content is the leaflet structure

    # The frontend page uses `project.name`, `project.molecule`, `project.therapeutic_area`, `project.benefits`
    # These come from the `project` object fetched from the `projects` table.
    # `project.molecule` was the old field name, new is `molecule_names`.
    # `project.benefits` was old, new is `key_differentiating_benefits`.
    # The frontend expects `insights.color_palette` to be a list of color objects.
    # The `generate_insights` produces a list: `{"name": "Blue", "hex": "#0000FF", "reason": "..."}`.
    # If `insight_color_palette` stores this list directly in its `content`, then `insights_data["color_palette"]` will be that list.
    # The frontend expects `brand_package.brand_names[0]`. We are providing `brand_name_suggestions` which is a list of dicts.
    # The frontend expects `brand_package.slogans[0].en`. We are providing `slogans` which is a list of dicts.
    # The frontend expects `brand_package.leaflet_json.sections[0].content`. We provide `leaflet_draft`.

    # Let's adjust the output slightly to better match frontend expectations where easy.
    # The frontend uses `project.molecule`, but DB has `molecule_names`. Add `molecule` for compatibility for now.
    project["molecule"] = project.get("molecule_names")
    project["benefits"] = project.get("key_differentiating_benefits")

    # Frontend expects insights.color_palette to be a list of color objects.
    # Our `generate_insights` produces: `{"name": "Blue", "hex": "#0000FF", "reason": "..."}` (this is for one color, it returns a list of these)
    # Our `main.py` (create) stores this list as content of "insight_color_palette".
    # So `insights_data["color_palette"]` here should be that list. This matches frontend's `insights?.color_palette?.map(...)`.

    # Frontend uses `brand_package.brand_names?.[0]`. We have `brand_name_suggestions` (list of `{"name": "..."}`).
    # Let's add a `brand_names` field to `brand_package_data` for easier frontend use for now.
    brand_package_data["brand_names"] = [sug.get("name") for sug in brand_package_data["brand_name_suggestions"] if sug.get("name")]

    # Frontend uses `brand_package.slogans?.[0]?.en`. Our `slogans` is already `[{"english": "...", "bengali": "..."}]`. This matches.
    # Renaming "english" to "en" if needed by frontend: The frontend uses `slogans[0].en`. Our AI produces `slogan_en`.
    # The `generate_brand_package` produces `slogans: [{"en": slogan_en, "bn": slogan_bn}]`. This matches.

    # Frontend uses `brand_package.leaflet_json`. We have `leaflet_draft`.
    # Let's rename for frontend compatibility.
    brand_package_data["leaflet_json"] = brand_package_data.pop("leaflet_draft", None)

    # Frontend uses `brand_package.compliance_status`. This needs to be sourced, perhaps from leaflet_json or a separate element.
    # For now, the `compliance_check` endpoint updates `brand_elements` table, but it was an old structure.
    # This part needs to be re-thought for the new structure. For now, it will likely be missing or hardcoded.
    # The old `get_project` took it from `brand_elements[0]["compliance_status"]`.
    # Let's see if we stored it with leaflet_draft.
    # No, `create_project` doesn't explicitly store compliance_status.
    # The `compliance_check` endpoint updates a `compliance_status` field on `brand_elements` table.
    # We could try to find an element of type 'leaflet_draft' and get a top-level 'compliance_status' from its content if we stored it there.
    # Or, it could be a separate element_type like 'compliance_info'.
    # For now, this will be missing from brand_package_data. The frontend will show 'pending'.

    return {
        "project": project,
        "insights": insights_data,
        "brand_package": brand_package_data
    }
