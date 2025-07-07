-- Supabase Table Schemas for PharmaBrand AI

-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Projects Table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_name VARCHAR(255),
    molecule_names TEXT, -- Comma-separated or JSON array
    therapeutic_area VARCHAR(255),
    key_differentiating_benefits TEXT,
    status VARCHAR(50) DEFAULT 'draft', -- e.g., draft, in_progress, completed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Brand Elements Table
-- Stores individual components of a brand package
CREATE TABLE brand_elements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    element_type VARCHAR(50) NOT NULL, -- e.g., 'brand_name', 'logo_concept', 'slogan', 'leaflet_section'
    content JSONB, -- Flexible field to store different element data (text, URL, JSON structure)
    -- Example for logo_concept: {"name": "Concept 1", "image_url": "...", "prompt": "...", "palette_id": "..."}
    -- Example for brand_name: {"name": "Brandex"}
    -- Example for slogan: {"english": "...", "bengali": "..."}
    -- Example for leaflet_section: {"title": "Introduction", "text": "..."}
    is_selected BOOLEAN DEFAULT FALSE, -- Indicates if user has selected this element
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Assets Table
-- Stores generated files and links (logos, leaflets, brand guidelines)
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    brand_element_id UUID REFERENCES brand_elements(id) ON DELETE SET NULL, -- Optional link to a specific brand element
    asset_type VARCHAR(50) NOT NULL, -- e.g., 'logo_png', 'logo_svg', 'leaflet_pdf', 'leaflet_docx', 'brand_guidelines_pdf', 'layout_json'
    file_name VARCHAR(255),
    storage_path VARCHAR(1024), -- Path in Supabase Storage or external URL
    -- For DALL-E generated images, this could be the OpenAI URL initially, then moved to Supabase storage
    metadata JSONB, -- e.g., {'version': 1, 'source': 'DALL-E 3'}
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (RLS) - IMPORTANT for multi-tenant SaaS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE brand_elements ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;

-- Policies for RLS (Example: Users can only see their own data)
CREATE POLICY "Allow individual user access" ON users
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Allow individual user insert" ON users
    FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "Allow individual user project access" ON projects
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Allow individual user brand_elements access" ON brand_elements
    FOR ALL USING (EXISTS (SELECT 1 FROM projects WHERE projects.id = project_id AND projects.user_id = auth.uid()));

CREATE POLICY "Allow individual user assets access" ON assets
    FOR ALL USING (EXISTS (SELECT 1 FROM projects WHERE projects.id = project_id AND projects.user_id = auth.uid()));

-- Indexes for performance
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_brand_elements_project_id ON brand_elements(project_id);
CREATE INDEX idx_brand_elements_type ON brand_elements(element_type);
CREATE INDEX idx_assets_project_id ON assets(project_id);
CREATE INDEX idx_assets_type ON assets(asset_type);

-- Comments for integration points:
-- - `users.id` will be linked to Supabase Auth users (auth.uid()).
-- - `projects.molecule_names` might be better as JSONB if complex parsing is needed, or keep as TEXT for simplicity.
-- - `brand_elements.content` is JSONB to allow flexibility. Consider validating its structure based on `element_type` in application logic.
-- - `assets.storage_path` will store URLs to files in Supabase Storage. For DALL-E, this might initially be the temporary URL from OpenAI.
-- - Vector search capabilities (pgvector) would typically involve another table or extending existing ones, e.g., for embedding document chunks related to market data or clinical trials. This schema focuses on core project data.
--   A separate `knowledge_base_embeddings` table might look like:
--   CREATE TABLE knowledge_base_embeddings (
--       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--       document_source VARCHAR(255), -- e.g., 'EMPA-REG_summary.pdf', 'Bangladesh_pharma_report_2023.docx'
--       chunk_text TEXT,
--       embedding VECTOR(1536), -- Or dimension matching your embedding model
--       metadata JSONB -- e.g., {'page_number': 5, 'trial_name': 'EMPA-REG'}
--   );
--   CREATE INDEX idx_knowledge_base_embeddings_embedding ON knowledge_base_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100); -- Example index for pgvector
-- - For translation, the `slogan` in `brand_elements.content` has fields for `english` and `bengali`. Similar structure can be used for other translatable text.
-- - Compliance check against DGDA rules would happen before final export generation, likely by querying/validating text content within `brand_elements` (e.g., leaflet sections).
--   This might involve an external API call or a local rules engine. Results of compliance checks could be stored in `brand_elements.metadata` or a separate `compliance_checks` table.
