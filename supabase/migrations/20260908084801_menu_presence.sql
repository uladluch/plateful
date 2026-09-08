-- Есть ли позиция в меню сети сегодня.
--
-- Сид MenuStat снят в 2018 году, и половины позиций в меню уже нет. Скрывать
-- их нельзя — человек мог сохранить блюдо в заказ или прийти по истории, и
-- исчезновение выглядело бы как поломка. Поэтому не удаляем, а помечаем:
-- приложение уводит такие блюда в раздел «Archive» в конце меню.
--
-- Проверка живёт отдельной таблицей, а не колонкой в items: у неё своя дата
-- и свой источник, и кроул цифр её не трогает.

create table menu_presence (
  chain_id   bigint not null references chains(id) on delete cascade,
  ext_key    text not null,
  on_menu    boolean not null,
  checked_at timestamptz not null default now(),
  source     text,
  primary key (chain_id, ext_key)
);

comment on table menu_presence is
  'Наблюдение: есть ли позиция в меню сети. Заполняет check_menu_presence.py.';
