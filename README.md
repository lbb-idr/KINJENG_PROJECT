# KINJENG_PROJECT

**Platform Simulasi Multi-Agent untuk Riset Sosial**

KINJENG_PROJECT bikin simulasi sosial pakai AI. Kamu upload dokumen, terus AI bikin agen-agen virtual (orang-orang digital) yang punya kepribadian, ingatan, dan cara berpikir sendiri. Mereka bakal berinteraksi, ngobrol, debat — mirip dunia nyata. Hasilnya bisa kamu lihat dalam bentuk grafik, statistik, dan laporan PDF.

Gampangnya: **kamu kasih data → AI bikin masyarakat digital → mereka "hidup" dan berinteraksi → kamu lihat hasilnya.**

## Fitur

- **Simulasi Sosial** — Bikin agen AI dengan kepribadian beda-beda, mereka saling ngobrol dan berdebat
- **Graph Interaksi** — Lihat hubungan antar agen dalam bentuk peta visual
- **Debat Internal** — Setiap agen punya "suara" berbeda (rasional, emosional, dll) yang debat sebelum ambil keputusan
- **Statistik & Laporan** — Hasil simulasi diolah otomatis jadi tabel, grafik, dan laporan PDF
- **5 Tipe Simulasi** — Akademik, Politik, Pasar, Sosial, atau Kustom

## Tech Stack

| Stack | Teknologi |
|-------|-----------|
| Frontend | Vue 3 + Vite + D3.js |
| Backend | Python Flask + Gunicorn |
| Database | SQLite |
| Graph | Zep + Neo4j |

## Engine Simulasi

KINJENG_PROJECT pakai **[MiroFish](https://github.com/666ghj/MiroFish)** sebagai mesin simulasi utamanya. MiroFish adalah engine buat simulasi sosial AI yang udah mature. Didukung sama **[OASIS](https://github.com/camel-ai/oasis)** dari CAMEL-AI buat simulasi interaksi agen di platform sosial.

## Development

```bash
# Backend
cd backend
pip install -r requirements.txt
python run.py

# Frontend
cd frontend
npm install
npm run dev
```

## Deploy

Deployed on Railway: `https://mirofish-production-c68d.up.railway.app`

---

*Dibuat untuk #JuaraVibeCoding 2026 — Engine simulasi oleh [MiroFish](https://github.com/666ghj/MiroFish)*
