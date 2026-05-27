<p align="center">
  <img src="./static/image/kinjeng-preview.png" alt="KINJENG_PROJECT Logo" width="400"/>
</p>

<p align="center"><strong>Platform Simulasi Multi-Agent untuk Riset Sosial</strong></p>

KINJENG_PROJECT adalah platform simulasi sosial berbasis AI. Pengguna dapat mengunggah dokumen, kemudian sistem akan menciptakan agen-agen virtual yang memiliki kepribadian, ingatan, dan pola pikir masing-masing. Agen-agen ini akan berinteraksi, berdiskusi, dan berdebat satu sama lain — layaknya masyarakat nyata. Hasil simulasi dapat dilihat dalam bentuk grafik, statistik, dan laporan PDF.

Alur kerjanya: **unggah data → AI menciptakan masyarakat digital → agen berinteraksi → hasil siap dianalisis.**

## Filosofi

**Kinjeng** (capung dalam bahasa Jawa, termasuk dialek Indramayu) memiliki empat sifat yang menjadi fondasi proyek ini:

1. **Mata Majemuk** — Capung dapat melihat hampir 360° dengan presisi tinggi. Seperti itulah AI dalam platform ini: mampu mengamati dan memetakan dinamika sosial dari berbagai sudut pandang secara simultan, mengatasi keterbatasan survei manual yang sempit.

2. **Terbang Cepat & Lincah** — Capung adalah penerbang ulung: maju, mundur, melayang, bermanuver instan. Simulasi multi-agen bekerja dengan kecepatan yang sama — memangkas proses riset yang biasanya berminggu-minggu menjadi hitungan menit.

3. **Indikator Lingkungan** — Capung hanya hidup di ekosistem yang bersih dan seimbang. Platform ini menjadi alat untuk menguji "kesehatan" opini publik terhadap suatu isu atau kebijakan sebelum kebijakan tersebut diterapkan di dunia nyata.

4. **Metamorfosis** — Capung bertransformasi dari nimfa air menjadi serangga bersayap. Ini melambangkan transformasi metodologi riset: dari survei konvensional menuju simulasi berbasis kecerdasan buatan.

> *Menggunakan kearifan lokal nama "Kinjeng" untuk teknologi Multi-Agent Simulation menunjukkan bahwa inovasi global tetap bisa lahir dan membumi dari filosofi alam di sekitar kita.*

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
