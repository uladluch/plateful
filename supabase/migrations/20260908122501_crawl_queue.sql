-- Очередь работ по сетям: что разведать, что кроулить, что не окупается.
--
-- Разведка печатала результат в терминал и забывала его. Для одного запуска
-- руками это нормально, для агента, который приходит время от времени, — нет:
-- он заново обходил бы те же сайты, чтобы заново узнать, что Wendy's рисует
-- меню скриптом. Знание должно накапливаться в базе, иначе каждый запуск
-- начинается с нуля.

alter table items drop constraint if exists items_flags_known;
alter table items
  add constraint items_flags_known
  check (flags <@ array['kids','shareable','regional','seasonal']::text[]);

alter table chains
  add column probed_at   timestamptz,
  add column source_note text;

comment on column chains.probed_at is 'Когда последний раз смотрели, чем сеть отдаёт данные. Пусто — не смотрели.';
comment on column chains.source_note is 'Что показала разведка: какая разметка сработала или почему ничего не вышло.';

alter table chains drop constraint chains_source_kind_check;
alter table chains
  add constraint chains_source_kind_check
  check (source_kind in ('seed','json_in_html','next_data','json_api','pdf','manual',
                         -- Меню рисуется скриптом: в HTML его нет вовсе, общий
                         -- читатель бессилен, нужен браузер или гайд в PDF.
                         'rendered',
                         -- Сайт не пускает: 403, обрыв TLS или запрет robots.txt.
                         'blocked'));

create view crawl_queue
with (security_invoker = true) as
select
  c.slug, c.name, c.item_count, c.source_url, c.source_kind, c.status,
  c.probed_at, c.last_crawl_at, c.source_note,
  case
    when c.status <> 'active'                      then 'на паузе'
    when c.source_url is null                      then 'найти адрес меню'
    when c.probed_at is null                       then 'разведать'
    when c.source_kind in ('rendered','blocked')   then 'нужен другой способ'
    when c.last_crawl_at is null                   then 'кроулить'
    when c.last_crawl_at < now() - c.crawl_every   then 'кроулить'
    else 'свежее'
  end as todo,
  -- Крупные сети вперёд: их ищут чаще, и цена устаревшей цифры там выше.
  c.item_count as weight
from chains c;

comment on view crawl_queue is 'Что делать со следующей сетью. Агент читает отсюда, а не решает заново.';
