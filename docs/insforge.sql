-- Run this in the InsForge SQL console after enabling authenticated users.
create table if not exists investigations (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  root_cause text not null,
  namespace text,
  confidence integer not null check (confidence between 0 and 100),
  status text not null,
  diagnosis jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists investigations_user_created_idx
  on investigations (user_id, created_at desc);

insert into realtime.channels (pattern, description, enabled)
values ('investigations', 'Investigation history updates', true)
on conflict do nothing;

create or replace function publish_investigation_created()
returns trigger as $$
begin
  perform realtime.publish(
    'investigations',
    'investigation_created',
    jsonb_build_object('id', new.id, 'root_cause', new.root_cause, 'confidence', new.confidence, 'status', new.status)
  );
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists investigation_created_realtime on investigations;
create trigger investigation_created_realtime
  after insert on investigations
  for each row execute function publish_investigation_created();
