<p align="center">
  <img src="./static/image/kinjeng-preview.png" alt="KINJENG_PROJECT Logo" width="400"/>
</p>

<h1 align="center">KINJENG_PROJECT</h1>

<p align="center"><strong>Platform Simulasi Multi-Agent untuk Riset Sosial</strong></p>

KINJENG_PROJECT adalah platform simulasi sosial berbasis AI. Pengguna dapat mengunggah dokumen, kemudian sistem akan menciptakan agen-agen virtual yang memiliki kepribadian, ingatan, dan pola pikir masing-masing. Agen-agen ini akan berinteraksi, berdiskusi, dan berdebat satu sama lain — layaknya masyarakat nyata. Hasil simulasi dapat dilihat dalam bentuk grafik, statistik, dan laporan PDF.

Alur kerjanya: **unggah data → AI menciptakan masyarakat digital → agen berinteraksi → hasil siap dianalisis.**

## Fitur

- **Simulasi Multi-Agent** — Ciptakan agen AI dengan kepribadian beragam; mereka akan berkomunikasi dan berdebat secara otomatis
- **Graf Interaksi** — Visualisasi hubungan antar agen dalam bentuk peta jaringan
- **Debat Internal** — Setiap agen memiliki perspektif berbeda (rasional, emosional, sosial, dll) yang berdebat sebelum mengambil keputusan
- **Statistik & Laporan** — Hasil simulasi diolah menjadi tabel, grafik, dan laporan PDF
- **5 Jenis Simulasi** — Akademik, Politik, Pasar, Sosial, atau Kustom

## Tech Stack

| Stack | Teknologi |
|-------|-----------|
| Frontend | Vue 3 + Vite + D3.js |
| Backend | Python Flask + Gunicorn |
| Database | SQLite |
| Graph | Zep + Neo4j |

## Engine Simulasi

KINJENG_PROJECT menggunakan **[MiroFish](https://github.com/666ghj/MiroFish)** sebagai mesin simulasi multi-agent. MiroFish merupakan platform simulasi sosial berbasis AI yang telah mature dan didukung oleh **[OASIS](https://github.com/camel-ai/oasis)** dari CAMEL-AI untuk simulasi interaksi agen di platform sosial.

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
