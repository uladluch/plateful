-- Вывод разведки снимков — в базу, а не в терминал: следующий агент
-- читает, чем сайт сети отдаёт фотографии, а не разведывает заново.
-- Пишет probe_photo_sources.py --apply.
alter table chains
  add column photo_probed_at timestamptz,
  add column photo_probe jsonb;

comment on column chains.photo_probe is 'Разведка снимков: url, platforms, images, verdict — см. probe_photo_sources.py.';
