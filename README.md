# KINJENG_PROJECT

**Platform Simulasi Multi-Agent untuk Riset Sosial**

KINJENG_PROJECT adalah platform simulasi multi-agent untuk pemodelan sosiokultural berbasis kognisi agen kecerdasan buatan. Mengombinasikan graph pengetahuan interaktif dengan mesin rujukan sosiologis untuk menyajikan simulasi data sosial se-presisi mungkin.

## Fitur

- **Engine Simulasi V1.0** — Model simulasi kognitif agen sosiokultural
- **Graph Interaksi** — Visualisasi riil jaringan korelasi komunikasi
- **Consensus Debating** — Diskursus internal tandingan multi-perspektif
- **Tabulasi Analitik** — Statistik distribusi frekuensi & tabulasi silang
- **Laporan PDF** — Generate laporan simulasi otomatis

## Tech Stack

| Stack | Teknologi |
|-------|-----------|
| Frontend | Vue 3 + Vite + D3.js |
| Backend | Python Flask + Gunicorn |
| Database | SQLite |
| Graph | Zep + Neo4j |

## Simulasi

KINJENG_PROJECT menggunakan **[MiroFish](https://github.com/666ghj/MiroFish)** sebagai engine simulasi multi-agent inti. MiroFish adalah platform simulasi sosial berbasis agen kecerdasan buatan dengan arsitektur kognitif Inner Parliament, memori temporal, dan pipeline simulasi lengkap (graph → environment → simulasi → laporan → interaksi).

Engine simulasi MiroFish didukung oleh **[OASIS (Open Agent Social Interaction Simulations)](https://github.com/camel-ai/oasis)** dari CAMEL-AI untuk simulasi interaksi agen di platform sosial.

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
