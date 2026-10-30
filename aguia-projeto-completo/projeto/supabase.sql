-- Ranking global do jogo "Águia — Voo dos 20 Céus".
-- Cole no SQL Editor do Supabase (Project > SQL Editor > New query) e execute uma vez.

create table if not exists public.ranking (
  id         bigint generated always as identity primary key,
  name       text not null check (char_length(name) between 1 and 12),
  level      int  not null check (level between 1 and 20),
  -- Teto de pontos plausível para o nível alcançado (bônus de nível + coletas generosas).
  -- Uma pontuação acima disso só sai de um cliente adulterado e é recusada pelo banco.
  score      int  not null check (score between 1 and 100*level*level + 2500*level + 2500),
  created_at timestamptz not null default now()
);

create index if not exists ranking_score_idx on public.ranking (score desc);

alter table public.ranking enable row level security;

-- Qualquer visitante pode ler o ranking e enviar uma pontuação; ninguém pode editar ou apagar pelo site.
drop policy if exists "ranking_ler" on public.ranking;
create policy "ranking_ler" on public.ranking for select to anon using (true);

drop policy if exists "ranking_inserir" on public.ranking;
create policy "ranking_inserir" on public.ranking for insert to anon with check (true);

-- Se quiser limpar o ranking depois (por exemplo, apagar um nome impróprio), faça pelo painel do Supabase
-- (Table Editor) ou pelo SQL Editor: delete from public.ranking where name = '...';
