-- Add separate draft and published snapshots for safe CMS editing.
alter table public.portfolio_versions
  add column if not exists draft jsonb,
  add column if not exists published jsonb;

-- Existing rows, if any, use their current fields as the initial snapshot.
update public.portfolio_versions
set draft = jsonb_build_object(
      'slug', slug,
      'internal_name', internal_name,
      'headline', headline,
      'intro', intro,
      'project_ids', project_ids
    ),
    published = jsonb_build_object(
      'slug', slug,
      'internal_name', internal_name,
      'headline', headline,
      'intro', intro,
      'project_ids', project_ids
    )
where draft is null or published is null;

alter table public.portfolio_versions
  alter column draft set not null,
  alter column published set not null;
