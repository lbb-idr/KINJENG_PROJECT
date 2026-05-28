<p align="center">
  <img src="./static/image/kinjeng-preview.png" alt="KINJENG_PROJECT Logo" width="400"/>
</p>

<p align="center"><strong>Platform Simulasi Multi-Agent untuk Riset Sosial</strong></p>

KINJENG_PROJECT adalah platform simulasi sosial berbasis AI. Pengguna dapat mengunggah dokumen, kemudian sistem akan menciptakan agen-agen virtual yang memiliki kepribadian, ingatan, dan pola pikir masing-masing. Agen-agen ini akan berinteraksi, berdiskusi, dan berdebat satu sama lain — layaknya masyarakat nyata. Hasil simulasi dapat dilihat dalam bentuk grafik, statistik, dan laporan PDF.

Alur kerjanya: **unggah data → AI menciptakan masyarakat digital → agen berinteraksi → hasil siap dianalisis.**

## Filosofi

**Kinjeng** (capung dalam bahasa Jawa) memiliki empat sifat yang menjadi fondasi proyek ini:

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

### TribeV2 Integration — Per-Agent Cognitive Identity

Sistem identitas agen di KINJENG_PROJECT terinspirasi dari **[TRIBE v2](https://github.com/facebookresearch/tribev2)** (Meta FAIR, 2026), sebuah multimodal foundation model yang memprediksi aktivitas fMRI otak manusia dari stimulus video/audio/teks. Konsep kunci yang diadopsi:

| Konsep TribeV2 | Implementasi di KINJENG_PROJECT |
|----------------|----------------------------------|
| **SubjectLayers** — setiap subjek fMRI punya linear layer unik yang memetakan shared brain representation ke output spesifik | **AgentIdentitySignature** — setiap agen punya vektor identitas 15+ dimensi (MBTI, cognitive style, education, knowledge, IQ, opinion bias) yang memodulasi semua respons |
| **Typicality** — seberapa "standar" aktivasi otak seseorang vs rata-rata populasi | Setiap agen punya skor *typicality*: agen dengan kepribadian tertentu (e.g. Neuroticism tinggi) menghasilkan respons lebih idiosinkratik |
| **Multimodal feature extraction** — LLaMA 3.2 (text), V-JEPA2 (video), Wav2Vec-BERT (audio) | *Processing modality* — agen visual vs verbal punya preferensi cara berpikir berbeda, terinspirasi dari riset Kraemer et al. (2009) |

Selain TribeV2, sistem ini juga didasarkan pada riset neuroscience terkini:
- **Personality → Brain typicality**: Neuroticism/Harm Avoidance → lower brain typicality (Krauss et al., 2024-2025)
- **Cognitive Style → Neural Pathway**: Visualizers vs Verbalizers menggunakan jalur otak berbeda untuk stimulus linguistik yang sama (Kraemer et al., 2009)
- **Hierarchical Linguistic Prediction**: Otak memprediksi kata DAN kalimat secara simultan; higher-level representations diupdate hanya di sentence boundaries (Communications Biology, 2025)
- **Reading Experience → Neural Individuality**: Semakin banyak pengalaman membaca, semakin idiosinkratik pola otak saat membaca teks ekspositori (PMC, 2025)

Detail implementasi: `backend/app/services/agent_identity.py`

## Alur Simulasi (5 Fase)

Platform ini memiliki 5 fase berurutan untuk menjalankan simulasi multi-agent secara lengkap. Berikut detail setiap fase:

---

### Fase 1: Ontologi & Graph (Step1GraphBuild.vue)

**Tujuan:** Membaca dokumen yang diunggah, menghasilkan skema ontologi (tipe entitas dan relasi), lalu membangun knowledge graph.

| Sub-langkah | Proses |
|-------------|--------|
| 1.1 Generate Ontologi | `POST /api/graph/ontology/generate` — LLM (`OntologyGenerator`) menganalisis dokumen untuk menghasilkan daftar `entity_types` (misal: Peneliti, Dosen, Mahasiswa) dan `relation_types` (misal: meneliti, mengajar, belajar) |
| 1.2 Graph Build | `POST /api/graph/build` — `GraphBuilder` membaca ontologi, mengekstrak entitas dan relasi dari teks dokumen, lalu menyimpannya ke database grafik |
| 1.3 Polling Status | `GET /api/graph/<graph_id>/status` — Frontend memantau progres build secara real-time |

**LLM Calls:** 1 call untuk ontology generation (menganalisis dokumen → menghasilkan tipe entitas & relasi)

**Dihasilkan:**
- `uploads/graphs/<graph_id>/graph_builder_output.json` — data entitas & relasi (mode local)
- Knowledge graph di Zep Cloud / lokal

---

### Fase 2: Persiapan Simulasi — Profile & Config (Step2EnvSetup.vue)

Fase ini terdiri dari 2 langkah yang dijalankan berurutan:

#### Langkah 2a: Buat Simulasi (`POST /api/simulation/create`)

Membuat instance simulasi baru dengan konfigurasi platform:

```json
{
  "project_id": "proj_xxx",
  "graph_id": "kinjeng_xxx",
  "enable_twitter": true,
  "enable_reddit": true,
  "sim_type": "academic"
}
```

Parameter `sim_type` (5 jenis simulasi) mempengaruhi prompt LLM di semua langkah selanjutnya:
- `academic` — Riset ilmiah, publikasi, diskusi akademik
- `political` — Opini publik, kebijakan pemerintah, dinamika politik
- `market` — Perilaku konsumen, tren pasar, strategi bisnis
- `social` — Interaksi sosial, budaya, isu kemasyarakatan
- `custom` — Kebutuhan spesifik pengguna

#### Langkah 2b: Prepare Simulasi (`POST /api/simulation/prepare`)

**Proses asynchronous** yang terdiri dari 3 tahap LLM:

| Tahap | Progress | Service | Deskripsi |
|-------|----------|---------|-----------|
| 1. Baca Entity (0-20%) | `reading` | `ZepEntityReader` | Membaca dan memfilter entitas dari graph berdasarkan tipe yang ditentukan |
| 2. Generate Profile (20-70%) | `generating_profiles` | `OasisProfileGenerator` | Untuk setiap entitas, LLM menghasilkan profil agen: nama, username, bio, persona, MBTI, usia, gender, kognitif, pendidikan, dll. Dilakukan paralel (default 5 thread) |
| 3. Generate Config (70-90%) | `generating_config` | `SimulationConfigGenerator` | LLM menghasilkan 4 konfigurasi: (a) waktu/durasi, (b) event/initial posts, (c) aktivitas per agent, (d) platform Twitter/Reddit |

**Progress dimonitor via:** `POST /api/simulation/prepare/status` (frontend polling tiap 2 detik)

**Dihasilkan di `uploads/simulations/<sim_id>/`:**
| File | Format | Kegunaan |
|------|--------|----------|
| `state.json` | JSON | Status simulasi (`created → preparing → ready`) |
| `reddit_profiles.json` | JSON | Profil agen untuk platform Reddit |
| `twitter_profiles.csv` | CSV | Profil agen untuk platform Twitter (format OASIS) |
| `simulation_config.json` | JSON | Konfigurasi lengkap (waktu, event, agent, platform) |

---

### Fase 3: Jalankan Simulasi (Step3Simulation.vue)

**Tujuan:** Menjalankan simulasi multi-platform menggunakan OASIS engine.

#### Cara Kerja

```
Step3Simulation.vue
  → POST /api/simulation/start { platform: "parallel" }
    → SimulationRunner.start_simulation()
      → subprocess: run_parallel_simulation.py
        ├── run_twitter_simulation()   → OASIS TwitterEnv
        └── run_reddit_simulation()    → OASIS RedditEnv
```

#### Mekanisme Eksekusi

1. **Parallel execution:** Twitter dan Reddit dijalankan bersamaan via `asyncio.gather()`
2. **Simulation Loop:** Di setiap ronde:
   - Agen aktif dipilih berdasarkan waktu (peak/off-peak hours) dan activity_level
   - Setiap agen bisa melakukan: `CREATE_POST`, `REPLY`, `LIKE`, `REPOST`, `FOLLOW`
   - Interaksi disimpan ke SQLite database per platform
3. **D2 (Content Injection):** Postingan awal dari konfigurasi di-inject ke timeline
4. **D3 (Engagement Injection):** Like/repost awal untuk memicu diskusi
5. **Mini-rounds:** Agen aktif dipecah menjadi batch 3-5 per sub-round untuk simulasi lebih realistis
6. **Wait Mode:** Setelah semua ronde selesai, lingkungan tetap hidup menunggu perintah Interview

#### LLM Calls (oleh OASIS engine)
Setiap aksi agen (posting, reply, like, follow) memanggil LLM untuk memutuskan konten dan tindakan. Jumlah call ≈ agents_active × rounds × actions_per_round.

#### Progress Monitoring

| Feature | Endpoint | Interval |
|---------|----------|----------|
| Status umum | `GET /api/simulation/<id>/run-status` | 3 detik |
| Detail aksi | `GET /api/simulation/<id>/run-status/detail` | 5 detik |
| Riwayat aksi | `GET /api/simulation/<id>/actions?page=N` | Manual |
| Timeline ronde | `GET /api/simulation/<id>/timeline` | Manual |
| Statistik per agent | `GET /api/simulation/<id>/agent-stats` | Manual |
| Heartbeat | `POST /api/simulation/heartbeat/<id>` | 30 detik (auto-stop jika 5 menit tanpa heartbeat) |

#### File yang Dihasilkan

| File | Deskripsi |
|------|-----------|
| `twitter/actions.jsonl` | Semua aksi agen di Twitter (1 JSON per baris) |
| `reddit/actions.jsonl` | Semua aksi agen di Reddit |
| `simulation.log` | Log output subprocess |
| `run_state.json` | State runtime (round, actions, status) |
| `twitter_simulation.db` | Database OASIS Twitter |
| `reddit_simulation.db` | Database OASIS Reddit |
| `env_status.json` | Status IPC (`alive`/`stopped`) |

---

### Fase 4: Laporan (Step4Report.vue)

**Tujuan:** Menganalisis hasil simulasi dan menghasilkan laporan terstruktur menggunakan `ReportAgent` (LLM agentic).

#### Proses

```
Step4Report.vue
  → POST /api/report/generate
    → ReportAgent (LLM + Tools)
      ├── insight_forge — menemukan pola dan insight dari data aksi
      ├── detail_diver — menggali detail spesifik
      ├── evidence_collector — mengumpulkan bukti dari actions.jsonl
      ├── question_architect — merancang pertanyaan lanjutan
      └── graph_search — mencari data tambahan dari knowledge graph
```

Laporan dihasilkan **per-bagian** (section-by-section) sehingga frontend bisa menampilkan progres incremental.

#### Progress Monitoring

| Endpoint | Kegunaan |
|----------|----------|
| `GET /api/report/generate/status` | Status task utama |
| `GET /api/report/<id>/sections` | Daftar section yang sudah jadi (incremental) |
| `GET /api/report/<id>/section/<index>` | Isi satu section |
| `GET /api/report/<id>/agent-log` | Log aksi ReportAgent secara real-time |
| `GET /api/report/<id>/console-log` | Console log real-time |

#### File yang Dihasilkan

| File | Deskripsi |
|------|-----------|
| `uploads/reports/<report_id>/report.md` | Laporan lengkap (Markdown) |
| `uploads/reports/<report_id>/section_01.md` | Per-section files |
| `uploads/reports/<report_id>/meta.json` | Metadata laporan |
| `uploads/reports/<report_id>/agent_log.jsonl` | Log eksekusi ReportAgent |

---

### Fase 5: Interaksi & Wawancara (Step5Interaction.vue)

**Tujuan:** Dua mode interaksi pasca-simulasi — tanya jawab dengan ReportAgent tentang hasil, atau mewawancarai agen simulasi secara langsung.

#### Mode 1: Chat Laporan

`POST /api/report/chat` — Bertanya kepada ReportAgent tentang hasil simulasi. Agen menggunakan tools untuk mencari data di graph dan laporan.

#### Mode 2: Interview Agen (IPC)

Mewawancarai agen yang masih hidup di lingkungan simulasi (wait mode). Mekanisme:

```
Frontend → POST /api/simulation/interview
  → Backend tulis file: ipc_commands/<uuid>.json
    → OASIS subprocess baca file, panggil LLM untuk jawab
      → Tulis respons ke: ipc_responses/<uuid>.json
        → Backend polling sampai respons tersedia (timeout 60s)
          → Frontend tampilkan jawaban agen
```

**LLM Call:** LLM dipanggil dalam konteks persona agen — prefix prompt: *"结合你的人设、所有的过往记忆与行动，不调用任何工具直接用文本回复我："* agar agen menjawab sesuai karakter tanpa memanggil tools.

| Endpoint | Fungsi |
|----------|--------|
| `POST /api/simulation/interview` | Wawancara satu agen |
| `POST /api/simulation/interview/batch` | Wawancara batch |
| `POST /api/simulation/interview/all` | Tanya semua agen dengan pertanyaan sama |
| `GET /api/report/check/<sim_id>` | Cek apakah interview tersedia |

---

### Diagram Alur Lengkap

```
User Upload Dokumen
       ↓
FASE 1: Ontologi & Graph
  ├── LLM: Generate entity/relation types dari dokumen
  └── Build knowledge graph (Zep/Local)
       ↓
FASE 2: Persiapan Simulasi
  ├── 2a: Buat simulasi (pilih platform Twitter/Reddit)
  └── 2b: Prepare (async, 3 tahap LLM)
        ├── LLM: Baca entity dari graph
        ├── LLM: Generate profil agent (parallel)
        └── LLM: Generate konfigurasi simulasi
              ↓
FASE 3: Eksekusi Simulasi
  ├── Jalankan OASIS TwitterEnv + RedditEnv (parallel)
  ├── Setiap ronde: agent posting, reply, like, follow
  └── Simpan actions ke database SQLite + actions.jsonl
       ↓
FASE 4: Laporan
  ├── ReportAgent (LLM + 5 tools) analisis actions
  └── Hasilkan laporan section-by-section
       ↓
FASE 5: Interaksi
  ├── Chat dengan ReportAgent tentang hasil
  └── Interview agen simulasi via IPC
```

### Status Progres (State Machine)

```
Simulation  →  CREATED  →  PREPARING  →  READY  →  RUNNING  →  COMPLETED
                                                         ↓
                                                    FAILED / STOPPED
```

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

---

*Deploy info: Railway — internal only*

---

*Dibuat untuk #JuaraVibeCoding 2026 — Engine simulasi oleh [MiroFish](https://github.com/666ghj/MiroFish)*
