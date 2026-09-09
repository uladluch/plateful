/*
 * Снимок меню McDonald's — выполняется в браузере, на открытой странице
 * https://www.mcdonalds.com/us/en-us/about-our-food/nutrition-calculator.html
 *
 * Зачем браузер. На адреса `/dnaapp/…` curl и Python получают HTTP 000:
 * сеть смотрит на отпечаток рукопожатия TLS, и подделать его нечем.
 * Настоящая страница ходит по ним свободно — этим и пользуемся, ничего
 * не обходя: это те же запросы, что делает сам калькулятор, когда
 * человек листает меню.
 *
 * Как запустить:
 *   1. python3 backend/scripts/catch_snapshot.py backend/cache/mcdonalds.json
 *   2. открыть страницу калькулятора и выполнить этот файл в консоли
 *   3. Ctrl-C приёмнику
 *
 * Отдаём файл формой, а не fetch: страница закрывает `connect-src` своей
 * CSP, но `form-action` в ней не объявлен, и обычная отправка проходит.
 * Страница после этого уходит на ответ приёмника — так и задумано,
 * снимать больше нечего.
 */
(async () => {
  const PORT = 8977;
  const POOL = 6;

  const node = document.querySelector("[data-product-data]");
  if (!node) throw new Error("на странице нет data-product-data — не тот адрес?");
  const data = JSON.parse(node.getAttribute("data-product-data"));
  const products = data.products;

  // Позиция — это `itemId` размера. У однопорционных блюд размеров нет
  // вовсе, и там `itemId` равен ключу продукта: без этой ветки снимок
  // теряет все бургеры, включая Big Mac.
  const targets = new Map();          // itemId → продукт
  for (const [pid, product] of Object.entries(products)) {
    const sizes = (product.sizes || []).map(s => String(s.itemId)).filter(Boolean);
    for (const id of (sizes.length ? sizes : [String(pid)])) {
      if (!targets.has(id)) targets.set(id, product);
    }
  }

  // Раздел меню: витрины («McValue®») лежат первыми, поэтому храним все
  // разделы позиции, а выбирает уже адаптер.
  const sections = {};
  for (const category of data.categoryList) {
    sections[category.title] = [];
    for (const pid of (category.productId || [])) {
      const product = products[pid];
      if (!product) continue;
      const sizes = (product.sizes || []).map(s => String(s.itemId)).filter(Boolean);
      sections[category.title].push(...(sizes.length ? sizes : [String(pid)]));
    }
  }

  const records = [], failed = [];
  const ids = [...targets.keys()];
  let next = 0;

  async function take(id) {
    const url = `/dnaapp/itemDetails?country=US&language=en&showLiveData=true&item=${id}`;
    const answer = await fetch(url, { headers: { accept: "application/json" } })
                         .then(r => r.json());
    const item = answer.item || answer;
    const facts = (item.nutrient_facts || {}).nutrient || [];
    const by = {};
    for (const n of facts) {
      const value = parseFloat(n.value);
      if (!isNaN(value)) by[n.nutrient_name_id] = value;
    }
    // Веса порции сеть не публикует, но у каждого нутриента есть значение
    // на сто грамм продукта — отсюда вес и считается.
    const calories = facts.find(n => n.nutrient_name_id === "calories");
    let grams = null;
    if (calories) {
      const per100 = parseFloat(calories.hundred_g_per_product);
      const value = parseFloat(calories.value);
      if (per100 > 0 && value > 0) grams = Math.round(value / per100 * 100);
    }
    // Аллергены сеть пишет прозой, а следом — состав каждого компонента;
    // до первой точки идут именно аллергены.
    const allergen = typeof item.item_allergen === "string" ? item.item_allergen : "";
    const product = targets.get(id);
    records.push({
      id,
      n: item.item_name || product.title,
      cat: ((item.default_category || {}).category || {}).name || null,
      g: grams,
      img: String(product.desktopImageUrl || "").replace(/:nutrition-calculator-tile$/, ""),
      alg: allergen ? allergen.split(".")[0].split(",").map(s => s.trim().toLowerCase())
                              .filter(Boolean) : [],
      kcal: by.calories ?? null, protein: by.protein ?? null,
      carbs: by.carbohydrate ?? null, fat: by.fat ?? null,
      sat_fat: by.saturated_fat ?? null, trans_fat: by.trans_fat ?? null,
      cholesterol: by.cholesterol ?? null, sodium: by.sodium ?? null,
      sugar: by.sugars ?? null, fiber: by.fibre ?? by.fibre2015 ?? null,
    });
  }

  await Promise.all(Array.from({ length: POOL }, async () => {
    while (next < ids.length) {
      const id = ids[next++];
      try { await take(id); } catch (error) { failed.push(id); }
    }
  }));

  // Комбо-наборы этикетки не имеют: она зависит от выбранных стороны и
  // напитка, и `itemDetails` отдаёт пустой список нутриентов.
  const kept = records.filter(r => r.kcal !== null);
  console.log(`снято ${kept.length} из ${ids.length}` +
              `, без этикетки ${records.length - kept.length}` +
              `, не ответили ${failed.length}`);

  function send(payload) {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = `http://127.0.0.1:${PORT}/`;
    form.enctype = "text/plain";
    const field = document.createElement("textarea");
    field.name = "d";
    field.value = JSON.stringify(payload);
    form.appendChild(field);
    document.body.appendChild(form);
    form.submit();
  }

  // Разделы отправляем первыми: вторая отправка уводит страницу.
  window.__plateful = { items: kept, sections };
  console.log("готово. Отправьте разделы и позиции двумя запусками приёмника:\n" +
              "  send(window.__plateful.sections) → backend/cache/mcdonalds-sections.json\n" +
              "  send(window.__plateful.items)    → backend/cache/mcdonalds.json");
  window.__send = send;
})();
