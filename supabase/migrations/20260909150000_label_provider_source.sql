-- Сети публикуют этикетку не сами, а через подрядчика: закон о маркировке
-- меню обязывает раскрывать её, а считает и выкладывает данные Nutritionix
-- (Syndigo). Это отдельный вид источника: не сайт сети и не её гид, а
-- страница поставщика, куда сеть свои же цифры загружает.
--
-- Отличать его от прочих важно для честности: в карточке блюда мы
-- показываем, откуда цифра, и «взято у поставщика сети» — не то же самое,
-- что «взято с сайта сети».
alter table chains drop constraint chains_source_kind_check;
alter table chains add constraint chains_source_kind_check
  check (source_kind = any (array[
    'seed', 'json_in_html', 'next_data', 'json_api', 'pdf',
    'label_provider', 'manual', 'rendered', 'blocked']));

comment on column chains.source_kind is
  'Каким способом берутся данные сети: seed — срез MenuStat 2018;'
  ' json_in_html / next_data / json_api — разметка или API сайта сети;'
  ' pdf — её гид по питанию; label_provider — страница подрядчика, через'
  ' которого сеть публикует этикетку по закону о маркировке меню;'
  ' manual — правки руками; rendered / blocked — не читается.';
