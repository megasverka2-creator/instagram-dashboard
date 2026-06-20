// ============================================================================
//  EDDO — TV MENU  ·  BARCHA MA'LUMOTLAR SHU YERDA
//  Haqiqiy menyu (referens rasmlardan olingan). Narx/nom/tarkibni shu yerdan
//  o'zgartiring. price: raqam (so'm). cheese:true -> 🧀, chicken:true -> 🐔.
//  prices: [36000, {v:39000, cheese:true}]  -> ikkita narx (2-si pishloqli).
// ============================================================================

export const CONFIG = {
  brand: 'eddo',
  tagline: 'FAST FOOD',
  currency: "so'm",
  pageDurationMs: 10000, // har sahifa 10 sekund
};

export const PAGES = [
  // ----------------------------------------------------------------- 01
  {
    id: 'asosiy',
    kicker: 'MENYU · 01',
    title: 'Lavash · Burger · Hot-dog · Donar',
    layout: 'categories',
    cards: [
      {
        name: 'Lavash', img: '/images/lavash.png', emoji: '🌯',
        groups: [
          { label: 'Standart', rows: [
            { label: 'odatiy', prices: [36000, { v: 39000, cheese: true }] },
            { label: 'kids',   prices: [29000, { v: 32000, cheese: true }] },
          ] },
          { label: 'Tandir', rows: [
            { label: 'odatiy', prices: [38000, { v: 41000, cheese: true }] },
            { label: 'kids',   prices: [30000, { v: 33000, cheese: true }] },
          ] },
          { label: 'Sezar', chicken: true, rows: [
            { label: '', prices: [{ v: 34000, cheese: true }] },
          ] },
        ],
      },
      {
        name: 'Burger', img: '/images/burger.png', emoji: '🍔',
        rows: [
          { label: 'Gamburger',      prices: [29000] },
          { label: 'Chizburger',     cheese: true, prices: [32000] },
          { label: 'Dablburger',     prices: [40000] },
          { label: 'Dablchizburger', cheese: true, prices: [43000] },
        ],
      },
      {
        name: 'Hot-dog', img: '/images/hotdog.png', emoji: '🌭',
        rows: [
          { label: 'Kids hot-dog',    prices: [11000] },
          { label: 'Oddiy hot-dog',   prices: [17000] },
          { label: 'Shohona hot-dog', prices: [21000] },
          { label: 'Chicken hot-dog', chicken: true, prices: [21000] },
          { label: 'Kebab hot-dog',   prices: [30000] },
        ],
      },
      {
        name: 'Donar', img: '/images/donar.png', emoji: '🥙',
        rows: [
          { label: 'Donar',             prices: [32000] },
          { label: 'Donar',             cheese: true, prices: [35000] },
          { label: 'Donar (tarelkada)', prices: [39000] },
        ],
      },
    ],
  },

  // ----------------------------------------------------------------- 02
  {
    id: 'snek',
    kicker: 'MENYU · 02',
    title: 'Snek & Ichimlik',
    layout: 'snacks',
    cards: [
      { name: 'Klab Sendvich', img: '/images/klab.png', emoji: '🥪', chicken: true, rows: [{ label: 'sendvich', prices: [33000] }] },
      { name: 'Xaggi', img: '/images/xaggi.png', emoji: '🌯', rows: [
        { label: 'Xaggi', prices: [35000] },
        { label: 'Xaggi', cheese: true, prices: [38000] },
      ] },
      { name: 'Fri', img: '/images/fri.png', emoji: '🍟', rows: [{ label: '120 gr', prices: [15000] }] },
      { name: 'Naggetslar', img: '/images/naggets.png', emoji: '🍗', chicken: true, rows: [
        { label: '120 gr', prices: [17000] },
        { label: '300 gr', prices: [41000] },
      ] },
      { name: 'Qahva', emoji: '☕', rows: [
        { label: 'Qora', prices: [5000] },
        { label: '3 tasi 1 da', prices: [5000] },
      ] },
      { name: 'Salqin ichimliklar', emoji: '🥤', drinks: [
        { label: 'Pepsi',      sizes: ['0.5L', '1L', '1.5L'] },
        { label: 'Coca Cola',  sizes: ['0.5L', '1L', '1.5L'] },
        { label: 'Lipton',     sizes: ['0.5L', '1L', '1.5L'] },
        { label: 'Mineral suv',sizes: ['0.5L', '1L', '1.5L'] },
      ] },
    ],
    sauces: {
      title: 'Souslar', price: 5000,
      items: [
        { name: 'eddo', img: '/images/sous-eddo.png', emoji: '🥫' },
        { name: 'sarimsoqli', img: '/images/sous-sarimsoqli.png', emoji: '🧄' },
        { name: 'ketchup', img: '/images/sous-ketchup.png', emoji: '🍅' },
        { name: 'chili', img: '/images/sous-chili.png', emoji: '🌶️' },
        { name: 'mayonez', img: '/images/sous-mayonez.png', emoji: '🥚' },
      ],
    },
  },

  // ----------------------------------------------------------------- 03
  {
    id: 'kombo',
    kicker: 'MENYU · 03',
    title: 'Kombo Takliflar',
    layout: 'combos',
    cols: 3, rows: 2,
    cards: [
      { name: 'Kombo Lavash', img: '/images/kombo-lavash.png', emojis: ['🌯', '🍟', '🥤'], price: 52000, featured: true,
        items: ['Lavash', 'Pepsi 0.5l', 'Naggets 50gr', 'Fri 50gr', 'Sous'] },
      { name: 'Kombo Burger', img: '/images/kombo-burger.png', emojis: ['🍔', '🍟', '🥤'], price: 44000,
        items: ['Gamburger', 'Pepsi 0.5l', 'Naggets 50gr', 'Fri 50gr', 'Sous'] },
      { name: 'Kombo Klab', img: '/images/kombo-klab.png', emojis: ['🥪', '🍟', '🥤'], price: 48000,
        items: ['Sendvich', 'Pepsi 0.5l', 'Naggets 50gr', 'Fri 50gr', 'Sous'] },
      { name: 'Kombo Donar', img: '/images/kombo-donar.png', emojis: ['🥙', '🍟', '🥤'], price: 46000,
        items: ['Donar', 'Pepsi 0.5l', 'Naggets 50gr', 'Fri 50gr', 'Sous'] },
      { name: 'Kombo Snek', img: '/images/kombo-snek.png', emojis: ['🍗', '🍟', '🥤'], price: 28000,
        items: ['Naggets 120gr', 'Pepsi 0.5l', 'Fri 50gr', 'Sous'] },
      { name: 'Kombo Kids', img: '/images/kombo-kids.png', emojis: ['🌭', '🍟', '🧃'], price: 24000,
        items: ['Hot-dog Kids', 'Sok 0.25l', 'Naggets 50gr', 'Fri 50gr', 'Sous'] },
    ],
  },

  // ----------------------------------------------------------------- 04
  {
    id: 'pitsa-1',
    kicker: 'PITSA · 04',
    title: 'Pitsalar — I',
    layout: 'pizzas',
    cols: 3, rows: 2,
    cards: [
      { name: 'Pitsa Margarita', img: '/images/margarita.png', ru: 'Пицца Маргарита', emoji: '🍕',
        sizes: [{ label: '30 sm', price: 42000 }, { label: '35 sm', price: 52000 }] },
      { name: 'Pepperoni', img: '/images/pepperoni.png', ru: 'Пепперони', emoji: '🍕', featured: true,
        sizes: [{ label: '30 sm', price: 54000 }, { label: '35 sm', price: 69000 }] },
      { name: 'Kebab pitsa', img: '/images/kebab.png', ru: 'Пицца кебаб', emoji: '🍕',
        sizes: [{ label: '30 sm', price: 56000 }, { label: '35 sm', price: 68000 }] },
      { name: 'Tovuqli pitsa', img: '/images/tovuqli.png', ru: 'Куриная пицца', emoji: '🍕',
        sizes: [{ label: '30 sm', price: 52000 }, { label: '35 sm', price: 67000 }] },
      { name: 'Pitsa 50/50', img: '/images/50-50.png', ru: 'Пицца 50/50', emoji: '🍕',
        sizes: [{ label: '30 sm', price: 55000 }, { label: '35 sm', price: 70000 }] },
      { name: 'Julen pitsa', img: '/images/julen.png', ru: 'Жульен с курицей и грибами', emoji: '🍕',
        sizes: [{ label: '30 sm', price: 62000 }, { label: '35 sm', price: 77000 }] },
    ],
  },

  // ----------------------------------------------------------------- 05
  {
    id: 'pitsa-2',
    kicker: 'PITSA · 05',
    title: 'Pitsalar — II',
    layout: 'pizzas',
    cols: 3, rows: 2,
    cards: [
      { name: 'Birlashma', img: '/images/birlashma.png', ru: 'Комбинированная', emoji: '🍕',
        sizes: [{ label: '30 sm', price: 62000 }, { label: '35 sm', price: 76000 }] },
      { name: 'Pitsa 4 mavsum', img: '/images/4-mavsum.png', ru: 'Пицца 4 сезона', emoji: '🍕',
        sizes: [{ label: '30 sm', price: 63000 }, { label: '35 sm', price: 79000 }] },
      { name: 'Pitsa Assorti', img: '/images/assorti.png', ru: 'Пицца Ассорти', emoji: '🍕',
        sizes: [{ label: '30 sm', price: 63000 }, { label: '35 sm', price: 79000 }] },
      { name: 'Donar pitsa', img: '/images/donar-pitsa.png', ru: 'Донар пицца', emoji: '🍕',
        sizes: [{ label: '30 sm', price: 63000 }, { label: '35 sm', price: 79000 }] },
      { name: 'Shefdan kombo', img: '/images/shefdan.png', ru: 'Комбо от шефа', emoji: '🍕', featured: true,
        sizes: [{ label: '30 sm', price: 74000 }, { label: '35 sm', price: 91000 }] },
      { name: "Go'shtli pitsa", img: '/images/goshtli.png', ru: 'Мясная пицца с грибами', emoji: '🍕',
        sizes: [{ label: '30 sm', price: 75000 }, { label: '35 sm', price: 92000 }] },
    ],
  },

  // ----------------------------------------------------------------- 06
  {
    id: 'pitsa-kombo',
    kicker: 'PITSA · 06',
    title: 'Pitsa Kombolar',
    layout: 'combos',
    cols: 2, rows: 2,
    cards: [
      { name: 'Kombo Bolajon', img: '/images/kombo-bolajon.png', ru: 'Комбо Болажон', emojis: ['🍕', '🍟', '🥤'], price: 79000,
        items: ['Pepperoni (30sm)', 'Naggets 50gr', 'Pepsi 1l', 'Fri 50gr', 'Sous'] },
      { name: 'Kombo Mazza', img: '/images/kombo-mazza.png', ru: 'Комбо Мазза', emojis: ['🍕', '🍟', '🥤'], price: 77000,
        items: ['Tovuqli pitsa (30sm)', 'Naggets 50gr', 'Pepsi 1l', 'Fri 50gr', 'Sous'] },
      { name: 'Kombo Sevimli', img: '/images/kombo-sevimli.png', ru: 'Комбо Севимли', emojis: ['🍕', '🍟', '🥤'], price: 87000, featured: true,
        items: ['Donar pitsa (30sm)', 'Naggets 50gr', 'Pepsi 1l', 'Fri 50gr', 'Sous'] },
      { name: "Kombo Do'stlar", img: '/images/kombo-dostlar.png', ru: 'Комбо Дустлар', emojis: ['🍕', '🍟', '🥤'], price: 87000,
        items: ['Assorti pitsa (30sm)', 'Naggets 50gr', 'Pepsi 1l', 'Fri 50gr', 'Sous'] },
    ],
  },
];
