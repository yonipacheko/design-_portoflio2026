-- CMS persistence schema. Run after the portfolio_versions table exists.
create table if not exists public.cms_sessions (
  sid text primary key,
  user_id bigint not null,
  csrf text not null,
  expires bigint not null,
  created_at timestamptz not null default now()
);

alter table public.cms_sessions enable row level security;

create index if not exists cms_sessions_expires_idx
  on public.cms_sessions (expires);

-- The CMS server uses the Supabase service role. No browser-facing policies
-- are created here, so anonymous clients cannot read or write CMS data.
