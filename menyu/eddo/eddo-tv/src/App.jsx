import React, { useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CONFIG, PAGES } from './menuData'

/* ----------------------------------------------------------------- helpers */
const STAGE_W = 1920
const STAGE_H = 1080
const SIDE_PAD = 70
const CONTENT_TOP = 296
const CONTENT_BOTTOM = 968
const GAP = 28

const UZ_MONTHS = ['yanvar','fevral','mart','aprel','may','iyun','iyul','avgust','sentabr','oktabr','noyabr','dekabr']
const UZ_DAYS = ['Yakshanba','Dushanba','Seshanba','Chorshanba','Payshanba','Juma','Shanba']

const fmtPrice = (n) => typeof n === 'number' ? n.toLocaleString('ru-RU').replace(/,/g,' ') : n

function useStageScale() {
  const [s, setS] = useState(1)
  useEffect(() => {
    const fit = () => {
      const vw = Math.max(window.innerWidth, window.screen?.width || 0) || STAGE_W
      const vh = Math.max(window.innerHeight, window.screen?.height || 0) || STAGE_H
      setS(Math.min(vw / STAGE_W, vh / STAGE_H))
    }
    fit()
    window.addEventListener('resize', fit)
    return () => window.removeEventListener('resize', fit)
  }, [])
  return s
}
function useClock() {
  const [now, setNow] = useState(new Date())
  useEffect(() => { const t = setInterval(() => setNow(new Date()), 1000); return () => clearInterval(t) }, [])
  return now
}

/* ----------------------------------------------------------------- tags */
const Cheese = ({ s = 20 }) => <span style={{ fontSize: s }} className="leading-none">🧀</span>
const Chicken = ({ s = 30 }) => (
  <span className="inline-grid place-items-center rounded-full bg-gold-400 shadow-sm"
        style={{ width: s, height: s }}>
    <span style={{ fontSize: s * 0.6 }} className="leading-none">🐔</span>
  </span>
)

// Renders a real image if `src` looks like a path/URL/data-URI, otherwise the emoji.
const isImage = (v) => typeof v === 'string' && /[./]/.test(v)
function Pic({ src, emoji, size, float = false, className = '' }) {
  const cls = `${float ? 'eddo-float ' : ''}${className}`
  const shadow = 'drop-shadow(0 12px 18px rgba(0,0,0,0.24))'
  if (isImage(src)) {
    return <img src={src} alt="" className={`${cls} object-contain`} style={{ height: size, width: size, filter: shadow }} />
  }
  return <span className={`${cls} leading-none`} style={{ fontSize: size, filter: shadow }}>{emoji}</span>
}

/* ----------------------------------------------------------------- background */
function Background() {
  return (
    <div className="absolute inset-0 overflow-hidden bg-eddo-800">
      <div className="eddo-drift absolute -top-[20%] -left-[10%] h-[80%] w-[70%] rounded-full blur-[120px]"
           style={{ background: 'radial-gradient(circle,#9a52e6 0%,rgba(154,82,230,0) 70%)' }} />
      <div className="eddo-drift-2 absolute top-[28%] -right-[15%] h-[90%] w-[70%] rounded-full blur-[130px]"
           style={{ background: 'radial-gradient(circle,#5d1fbc 0%,rgba(93,31,188,0) 70%)' }} />
      <div className="eddo-drift absolute bottom-[-25%] left-[18%] h-[70%] w-[60%] rounded-full blur-[120px]"
           style={{ background: 'radial-gradient(circle,#7a32d6 0%,rgba(122,50,214,0) 70%)' }} />
      <div className="absolute -top-[10%] left-1/2 h-[38%] w-[55%] -translate-x-1/2 rounded-full blur-[140px] opacity-20"
           style={{ background: 'radial-gradient(circle,#ffd60a 0%,rgba(255,214,10,0) 70%)' }} />
      <div className="absolute inset-0 opacity-[0.05]"
           style={{ backgroundImage: 'radial-gradient(#fff 1.4px,transparent 1.4px)', backgroundSize: '46px 46px' }} />
      <div className="eddo-grain absolute inset-0 opacity-[0.05] mix-blend-overlay" />
    </div>
  )
}

/* ----------------------------------------------------------------- header */
function Header({ now }) {
  const hh = String(now.getHours()).padStart(2,'0')
  const mm = String(now.getMinutes()).padStart(2,'0')
  const ss = String(now.getSeconds()).padStart(2,'0')
  const dateStr = `${now.getDate()}-${UZ_MONTHS[now.getMonth()]}, ${UZ_DAYS[now.getDay()]}`
  return (
    <div className="flex items-center justify-between px-[70px] pt-[42px]">
      <div className="flex items-center gap-4">
        <div className="relative grid h-[82px] w-[82px] place-items-center rounded-[24px] bg-gradient-to-br from-gold-400 to-gold-600 shadow-[0_14px_38px_rgba(245,163,0,0.5)]">
          <span className="font-display text-[44px] font-bold leading-none text-eddo-900">e</span>
          <span className="absolute -right-1.5 -top-1.5 h-4 w-4 rounded-full bg-white shadow" />
        </div>
        <div className="leading-none">
          <div className="font-display text-[50px] font-bold lowercase tracking-tight text-white">{CONFIG.brand}</div>
          <div className="mt-1 font-body text-[18px] font-extrabold tracking-[0.42em] text-gold-400">{CONFIG.tagline}</div>
        </div>
      </div>
      <div className="text-right">
        <div className="flex items-end justify-end gap-1 font-display font-semibold leading-none text-white">
          <span className="text-[62px]">{hh}:{mm}</span>
          <span className="mb-2 text-[26px] text-gold-400">{ss}</span>
        </div>
        <div className="mt-1.5 font-body text-[21px] font-bold capitalize text-white/70">{dateStr}</div>
      </div>
    </div>
  )
}

/* ----------------------------------------------------------------- price list (rows) */
function PriceRow({ row, fs = 21 }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-[3px]">
      <div className="flex items-center gap-2 truncate">
        <span className="font-body font-bold text-ink/85 truncate" style={{ fontSize: fs }}>{row.label}</span>
        {row.cheese && <Cheese s={fs * 0.85} />}
        {row.chicken && <Chicken s={fs * 1.25} />}
      </div>
      <div className="flex shrink-0 items-baseline gap-3">
        {row.prices.map((p, i) => {
          const v = typeof p === 'object' ? p.v : p
          const isCheese = typeof p === 'object' && p.cheese
          return (
            <span key={i} className="flex items-baseline gap-1 font-display font-bold text-ink" style={{ fontSize: fs * 1.12 }}>
              {isCheese && <Cheese s={fs * 0.8} />}{fmtPrice(v)}
            </span>
          )
        })}
      </div>
    </div>
  )
}

/* white card shell */
function CardShell({ children, w, h, featured, className = '', pad = 'p-7' }) {
  return (
    <motion.div variants={cardVariants} style={{ width: w, height: h }}
      className={`relative overflow-hidden rounded-[32px] ${className}`}>
      <div className="absolute inset-0 rounded-[32px] bg-white shadow-[0_22px_50px_-16px_rgba(20,4,46,0.65)]" />
      {featured && <div className="eddo-halo absolute inset-0 rounded-[32px] bg-gradient-to-br from-gold-400/55 to-gold-600/25 blur-md" />}
      <div className="absolute inset-0 rounded-[32px] ring-1 ring-eddo-900/5" />
      <div className={`relative z-10 flex h-full w-full flex-col ${pad}`}>{children}</div>
    </motion.div>
  )
}

/* ----------------------------------------------------------------- CATEGORY card (page 1) */
function CategoryCard({ card, w, h }) {
  const fs = 20
  const hasImg = isImage(card.img)
  const imgSize = Math.min(h * 0.64, 200)
  return (
    <CardShell w={w} h={h} pad="px-8 py-5">
      <div className="flex h-full items-stretch gap-4">
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="mb-1 flex items-center gap-3">
            {!hasImg && <span className="text-[34px] leading-none">{card.emoji}</span>}
            <span className="font-display text-[38px] font-bold leading-none text-ink">{card.name}</span>
            {card.chicken && <Chicken s={34} />}
          </div>
          <div className="flex flex-1 flex-col justify-center">
            {card.groups ? card.groups.map((g, gi) => {
              const inline = g.rows.length === 1 && g.rows[0].label === ''
              return (
                <div key={gi} className="mb-1">
                  <div className="mb-[2px] flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="rounded-md bg-gold-400 px-2.5 py-[2px] font-body text-[17px] font-extrabold text-ink">{g.label}</span>
                      {g.chicken && <Chicken s={26} />}
                    </div>
                    {inline && (
                      <div className="flex items-baseline gap-1 font-display font-bold text-ink" style={{ fontSize: fs * 1.12 }}>
                        {g.rows[0].prices.map((p, i) => {
                          const v = typeof p === 'object' ? p.v : p
                          const isCheese = typeof p === 'object' && p.cheese
                          return <span key={i} className="flex items-baseline gap-1">{isCheese && <Cheese s={fs * 0.8} />}{fmtPrice(v)}</span>
                        })}
                      </div>
                    )}
                  </div>
                  {!inline && g.rows.map((r, ri) => <PriceRow key={ri} row={r} fs={fs} />)}
                </div>
              )
            }) : card.rows.map((r, ri) => <PriceRow key={ri} row={r} fs={fs} />)}
          </div>
        </div>
        {hasImg && (
          <div className="grid flex-none place-items-center" style={{ width: imgSize + 6 }}>
            <Pic src={card.img} emoji={card.emoji} size={imgSize} float />
          </div>
        )}
      </div>
    </CardShell>
  )
}

/* ----------------------------------------------------------------- SNACK card (page 2) */
function SnackCard({ card, w, h }) {
  const imgSize = Math.min(h * 0.54, 128)
  return (
    <CardShell w={w} h={h} pad="px-7 py-5">
      <div className="flex items-center gap-3">
        <span className="font-display text-[30px] font-bold leading-none text-ink">{card.name}</span>
        {card.chicken && <Chicken s={28} />}
      </div>
      <div className="mt-1 flex flex-1 items-center gap-5">
        <div className="grid flex-none place-items-center" style={{ width: imgSize + 12 }}>
          <div className="absolute rounded-full bg-eddo-700/8" style={{ height: imgSize + 10, width: imgSize + 10 }} />
          <Pic src={card.img} emoji={card.emoji} size={imgSize} float className="relative" />
        </div>
        <div className="flex-1">
          {card.rows && card.rows.map((r, i) => <PriceRow key={i} row={r} fs={20} />)}
          {card.drinks && (
            <div className="space-y-1">
              {card.drinks.map((d, i) => (
                <div key={i} className="flex items-baseline gap-2">
                  <span className="font-body text-[18px] font-bold text-ink">{d.label}</span>
                  <span className="font-body text-[16px] font-semibold text-inksoft">{d.sizes.join(' · ')}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </CardShell>
  )
}

/* ----------------------------------------------------------------- SAUCE strip (page 2) */
function SauceStrip({ sauces, w, h }) {
  return (
    <CardShell w={w} h={h} pad="px-8 py-4">
      <div className="flex h-full items-center gap-6">
        <div className="flex flex-none flex-col">
          <span className="font-display text-[34px] font-bold leading-none text-ink">{sauces.title}</span>
          <span className="mt-1 font-body text-[16px] font-extrabold tracking-wide text-inksoft">har biri</span>
        </div>
        <div className="flex flex-1 items-center justify-around">
          {sauces.items.map((it, i) => (
            <div key={i} className="flex flex-col items-center gap-1">
              <div className="eddo-float" style={{ animationDelay: `${i * 0.35}s` }}><Pic src={it.img} emoji={it.emoji} size={56} /></div>
              <span className="font-body text-[20px] font-bold text-ink">{it.name}</span>
              <span className="rounded-full bg-gold-400 px-4 py-1 font-display text-[20px] font-bold text-ink shadow">{fmtPrice(sauces.price)}</span>
            </div>
          ))}
        </div>
      </div>
    </CardShell>
  )
}

/* ----------------------------------------------------------------- COMBO card (page 3 & 6) */
function ComboCard({ card, w, h }) {
  const big = w > 700
  const inner = w - (big ? 80 : 64)
  const tile = Math.min(h - 44, inner * 0.46, big ? 300 : 240)
  const titleFs = big ? 36 : 30
  const ruFs = big ? 18 : 15
  const itemFs = big ? 19 : 18
  const priceFs = big ? 40 : 34
  const curFs = big ? 20 : 16
  return (
    <CardShell w={w} h={h} featured={card.featured} pad={big ? 'px-9 py-5' : 'px-7 py-5'}>
      <div className="flex h-full items-stretch gap-3">
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="font-display font-bold leading-none text-ink" style={{ fontSize: titleFs }}>{card.name}</div>
          {card.ru && <div className="mt-1 font-body font-semibold text-inksoft" style={{ fontSize: ruFs }}>{card.ru}</div>}
          <div className={`flex flex-1 flex-col justify-center ${big ? 'mt-1 gap-0.5' : 'mt-3 gap-1.5'}`}>
            {card.items.map((it, i) => (
              <div key={i} className="flex items-center gap-2.5">
                <span className="h-2 w-2 flex-none rounded-full bg-gold-500" />
                <span className="font-body font-bold text-ink/80" style={{ fontSize: itemFs }}>{it}</span>
              </div>
            ))}
          </div>
          <motion.div variants={badgeVariants} className="mt-2 self-start">
            <div className={`flex items-baseline gap-2 rounded-2xl bg-gradient-to-br from-gold-400 to-gold-500 px-7 ${big ? 'py-2' : 'py-2.5'} shadow-[0_12px_26px_-6px_rgba(245,163,0,0.7)]`}>
              <span className="font-display font-bold leading-none text-ink" style={{ fontSize: priceFs }}>{fmtPrice(card.price)}</span>
              <span className="font-body font-extrabold text-ink/70" style={{ fontSize: curFs }}>{CONFIG.currency}</span>
            </div>
          </motion.div>
        </div>
        <div className="grid flex-none place-items-center" style={{ width: tile }}>
          {isImage(card.img) ? (
            <Pic src={card.img} emoji="" size={tile} float className="relative" />
          ) : (
            <div className="flex gap-1.5">
              {card.emojis.map((e, i) => (
                <span key={i} className="eddo-float leading-none" style={{ fontSize: big ? 46 : 34, animationDelay: `${i * 0.4}s` }}>{e}</span>
              ))}
            </div>
          )}
        </div>
      </div>
    </CardShell>
  )
}

/* ----------------------------------------------------------------- PIZZA card (page 4 & 5) */
function PizzaCard({ card, w, h }) {
  const imgSize = Math.min(h * 0.80, 222)
  const nameFs = Math.min(w * 0.07, 36)
  return (
    <CardShell w={w} h={h} featured={card.featured} pad="px-6 py-5">
      <div className="flex h-full items-center gap-4">
        <div className="grid flex-none place-items-center" style={{ width: imgSize, height: imgSize }}>
          <div className="absolute rounded-full bg-eddo-700/8" style={{ height: imgSize * 0.96, width: imgSize * 0.96 }} />
          <Pic src={card.img} emoji={card.emoji} size={imgSize * 0.94} float className="relative" />
        </div>
        <div className="flex min-w-0 flex-1 flex-col justify-center">
          <div className="font-display font-bold leading-tight text-ink" style={{ fontSize: nameFs }}>{card.name}</div>
          {card.ru && <div className="mt-1 font-body text-[15px] font-semibold text-inksoft">{card.ru}</div>}
          <div className="mt-3 flex flex-col gap-2">
            {card.sizes.map((s, i) => {
              const hot = i === card.sizes.length - 1
              return (
                <motion.div key={i} variants={badgeVariants}
                  className={`flex items-center justify-between rounded-xl px-4 py-2 ${hot ? 'bg-gold-400 shadow-[0_6px_16px_-6px_rgba(245,163,0,0.7)]' : 'bg-eddo-900/[0.06]'}`}>
                  <span className={`font-body text-[16px] font-extrabold tracking-wide ${hot ? 'text-ink/70' : 'text-inksoft'}`}>{s.label}</span>
                  <span className="font-display text-[28px] font-bold leading-none text-ink">{fmtPrice(s.price)}</span>
                </motion.div>
              )
            })}
          </div>
        </div>
      </div>
    </CardShell>
  )
}

/* ----------------------------------------------------------------- motion variants */
const cardVariants = {
  hidden: { opacity: 0, y: 42, scale: 0.95 },
  show: { opacity: 1, y: 0, scale: 1, transition: { type: 'spring', stiffness: 220, damping: 24 } },
}
const badgeVariants = {
  hidden: { scale: 0, opacity: 0 },
  show: { scale: 1, opacity: 1, transition: { type: 'spring', stiffness: 520, damping: 16, delay: 0.2 } },
}
const container = { hidden: {}, show: { transition: { staggerChildren: 0.08, delayChildren: 0.3 } } }

/* ----------------------------------------------------------------- slide */
function gridGeom(cols, rows, areaTop = CONTENT_TOP, areaBottom = CONTENT_BOTTOM) {
  const areaW = STAGE_W - SIDE_PAD * 2
  const areaH = areaBottom - areaTop
  return {
    areaW, areaH,
    cardW: (areaW - GAP * (cols - 1)) / cols,
    cardH: (areaH - GAP * (rows - 1)) / rows,
  }
}

function SlideBody({ page }) {
  if (page.layout === 'categories') {
    const { cardW, cardH } = gridGeom(2, 2)
    return (
      <motion.div variants={container} initial="hidden" animate="show"
        className="absolute flex flex-wrap content-center justify-center"
        style={{ left: SIDE_PAD, right: SIDE_PAD, top: CONTENT_TOP, bottom: STAGE_H - CONTENT_BOTTOM, gap: GAP }}>
        {page.cards.map((c) => <CategoryCard key={c.name} card={c} w={cardW} h={cardH} />)}
      </motion.div>
    )
  }

  if (page.layout === 'snacks') {
    const sauceH = 150
    const gridBottom = CONTENT_BOTTOM - sauceH - GAP
    const { cardW, cardH } = gridGeom(3, 2, CONTENT_TOP, gridBottom)
    const areaW = STAGE_W - SIDE_PAD * 2
    return (
      <motion.div variants={container} initial="hidden" animate="show" className="absolute inset-0">
        <div className="absolute flex flex-wrap content-center justify-center"
          style={{ left: SIDE_PAD, right: SIDE_PAD, top: CONTENT_TOP, height: gridBottom - CONTENT_TOP, gap: GAP }}>
          {page.cards.map((c) => <SnackCard key={c.name} card={c} w={cardW} h={cardH} />)}
        </div>
        <div className="absolute" style={{ left: SIDE_PAD, top: gridBottom + GAP }}>
          <SauceStrip sauces={page.sauces} w={areaW} h={sauceH} />
        </div>
      </motion.div>
    )
  }

  if (page.layout === 'combos') {
    const { cardW, cardH } = gridGeom(page.cols, page.rows)
    return (
      <motion.div variants={container} initial="hidden" animate="show"
        className="absolute flex flex-wrap content-center justify-center"
        style={{ left: SIDE_PAD, right: SIDE_PAD, top: CONTENT_TOP, bottom: STAGE_H - CONTENT_BOTTOM, gap: GAP }}>
        {page.cards.map((c) => <ComboCard key={c.name} card={c} w={cardW} h={cardH} />)}
      </motion.div>
    )
  }

  if (page.layout === 'pizzas') {
    const { cardW, cardH } = gridGeom(page.cols, page.rows)
    return (
      <motion.div variants={container} initial="hidden" animate="show"
        className="absolute flex flex-wrap content-center justify-center"
        style={{ left: SIDE_PAD, right: SIDE_PAD, top: CONTENT_TOP, bottom: STAGE_H - CONTENT_BOTTOM, gap: GAP }}>
        {page.cards.map((c) => <PizzaCard key={c.name} card={c} w={cardW} h={cardH} />)}
      </motion.div>
    )
  }
  return null
}

function Slide({ page }) {
  const titleSize = page.title.length > 22 ? 52 : 70
  return (
    <motion.div className="absolute inset-0"
      initial={{ opacity: 0, x: 70 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -70 }}
      transition={{ duration: 0.7, ease: [0.4, 0, 0.2, 1] }}>
      <div className="absolute left-[70px] right-[70px] top-[148px]">
        <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12, duration: 0.5 }}
          className="font-body text-[21px] font-black tracking-[0.4em] text-gold-400">{page.kicker}</motion.div>
        <motion.h1 initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.18, duration: 0.55 }}
          className="mt-1 flex items-center font-display font-bold leading-none text-white" style={{ fontSize: titleSize }}>
          {page.title}
          <span className="ml-5 inline-block h-3 w-16 rounded-full bg-gold-400" />
        </motion.h1>
      </div>
      <SlideBody page={page} />
    </motion.div>
  )
}

/* ----------------------------------------------------------------- progress */
function ProgressBar({ index, total, duration }) {
  return (
    <div className="absolute bottom-[34px] left-[70px] right-[70px]">
      <div className="flex items-center gap-3">
        {Array.from({ length: total }).map((_, i) => (
          <div key={i} className="relative h-[10px] flex-1 overflow-hidden rounded-full bg-white/15">
            {i < index && <div className="absolute inset-0 rounded-full bg-gold-400/85" />}
            {i === index && (
              <motion.div key={`fill-${index}`} className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-gold-400 to-gold-600"
                initial={{ width: '0%' }} animate={{ width: '100%' }} transition={{ duration: duration / 1000, ease: 'linear' }} />
            )}
          </div>
        ))}
        <div className="ml-3 font-display text-[24px] font-semibold tabular-nums text-white/80">
          {String(index + 1).padStart(2,'0')}<span className="text-white/35"> / {String(total).padStart(2,'0')}</span>
        </div>
      </div>
    </div>
  )
}

/* ----------------------------------------------------------------- app */
export default function App() {
  const scale = useStageScale()
  const now = useClock()
  const [index, setIndex] = useState(0)
  const total = PAGES.length
  useEffect(() => {
    const t = setTimeout(() => setIndex((i) => (i + 1) % total), CONFIG.pageDurationMs)
    return () => clearTimeout(t)
  }, [index, total])
  const page = useMemo(() => PAGES[index], [index])

  return (
    <div className="fixed inset-0 overflow-hidden bg-eddo-950">
      <div className="relative overflow-hidden font-body"
        style={{ width: STAGE_W, height: STAGE_H, transform: `scale(${scale})`, transformOrigin: 'top left', position: 'absolute', top: 0, left: 0 }}>
        <Background />
        <div className="relative z-10 h-full w-full">
          <Header now={now} />
          <AnimatePresence><Slide key={page.id} page={page} /></AnimatePresence>
          <ProgressBar index={index} total={total} duration={CONFIG.pageDurationMs} />
        </div>
      </div>
    </div>
  )
}
