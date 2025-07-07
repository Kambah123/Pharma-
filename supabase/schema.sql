-- Supabase schema for PharmaBrand AI

create table users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  created_at timestamp with time zone default timezone('utc', now())
);

create table projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id),
  name text,
  molecule text,
  therapeutic_area text,
  benefits text,
  prompt text,
  created_at timestamp with time zone default timezone('utc', now())
);

-- Brand elements for a project (brand package)
create table brand_elements (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id),
  user_id uuid references users(id),
  brand_name text,
  logo_url text,
  slogan_en text,
  slogan_bn text,
  color_palette jsonb,
  leaflet_json jsonb,
  compliance_status text, -- e.g. 'pending', 'approved', 'rejected'
  created_at timestamp with time zone default timezone('utc', now())
);

-- Persistent AI-generated insights per project
create table insights (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id),
  user_id uuid references users(id),
  competitors jsonb,
  brand_positioning text,
  color_palette jsonb,
  clinical_trials jsonb,
  created_at timestamp with time zone default timezone('utc', now())
);

-- Assets (files, images, exports)
create table assets (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id),
  user_id uuid references users(id),
  type text, -- 'logo', 'leaflet', etc.
  url text,
  created_at timestamp with time zone default timezone('utc', now())
);

