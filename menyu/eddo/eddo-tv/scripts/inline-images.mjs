import { readFileSync, writeFileSync, readdirSync } from 'fs'
import { join } from 'path'

const htmlPath = 'dist/index.html'
const imgDir = 'public/images'
let html = readFileSync(htmlPath, 'utf8')

const mime = (f) => f.endsWith('.png') ? 'image/png'
  : f.endsWith('.webp') ? 'image/webp'
  : f.endsWith('.jpg') || f.endsWith('.jpeg') ? 'image/jpeg' : 'application/octet-stream'

// longest names first to avoid partial overlaps
const files = readdirSync(imgDir).sort((a, b) => b.length - a.length)
let count = 0
for (const f of files) {
  const data = readFileSync(join(imgDir, f)).toString('base64')
  const uri = `data:${mime(f)};base64,${data}`
  const needle = `/images/${f}`
  if (html.includes(needle)) {
    html = html.split(needle).join(uri)
    count++
  }
}
writeFileSync(htmlPath, html)
console.log(`inlined ${count} images into ${htmlPath}`)
