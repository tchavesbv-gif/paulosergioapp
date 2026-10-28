-- 1. Criar ou substituir as funções RPC no esquema public
create or replace function public.api_listar_demandas()
returns setof public.pacientes_demandas
language sql security definer as $$
    select * from public.pacientes_demandas order by id desc;
$$;

create or replace function public.api_inserir_demanda(
    p_nome text,
    p_telefone text,
    p_cartao_sus text,
    p_demanda text,
    p_reportado text
)
returns void
language plpgsql security definer as $$
declare
    v_status text;
begin
    if p_reportado is not null and trim(p_reportado) <> '' then
        v_status := 'Delegado';
    else
        v_status := 'Em Aberto';
    end if;

    insert into public.pacientes_demandas (
        nome, telefone, cartao_sus, demanda, reportado, status
    ) values (
        p_nome, p_telefone, p_cartao_sus, p_demanda, p_reportado, v_status
    );
end;
$$;

create or replace function public.api_atualizar_status(
    p_id int8,
    p_status text
)
returns void
language plpgsql security definer as $$
begin
    update public.pacientes_demandas
    set status = p_status,
        data_resolucao = case when p_status = 'Encerrado' then now() else null end
    where id = p_id;
end;
$$;

-- 2. Conceder permissões de execução
grant execute on function public.api_listar_demandas() to anon, authenticated, service_role;
grant execute on function public.api_inserir_demanda(text, text, text, text, text) to anon, authenticated, service_role;
grant execute on function public.api_atualizar_status(int8, text) to anon, authenticated, service_role;

-- 3. Forçar o PostgREST a atualizar o cache
notify pgrst, 'reload schema';
