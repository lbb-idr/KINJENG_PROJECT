# Bersihkan MiroFish dari KINJENG_PROJECT
# Hanya ubah yang visible/eksternal, internal tetap aman

$root = "E:\GEMINI_PROJECT\MIROFISH PROJECT"

# === FRONTEND: Brand text ===
$brandViews = @(
    "$root\frontend\src\views\InteractionView.vue",
    "$root\frontend\src\views\MainView.vue",
    "$root\frontend\src\views\ReportView.vue",
    "$root\frontend\src\views\SimulationRunView.vue",
    "$root\frontend\src\views\SimulationView.vue",
    "$root\frontend\src\views\SurveyResultsView.vue"
)

foreach ($f in $brandViews) {
    (Get-Content $f) -replace '<div class="brand"[^>]*>MIROFISH</div>', '<div class="brand" @click="router.push(\''/\'')">KINJENG</div>' | Set-Content $f
}

# === FRONTEND: Storage keys ===
(Get-Content "$root\frontend\src\views\ReportView.vue") -replace "'mirofish_report'", "'kinjeng_report'" | Set-Content "$root\frontend\src\views\ReportView.vue"
(Get-Content "$root\frontend\src\views\SimulationRunView.vue") -replace "'mirofish_sim_run'", "'kinjeng_sim_run'" | Set-Content "$root\frontend\src\views\SimulationRunView.vue"
(Get-Content "$root\frontend\src\views\SimulationView.vue") -replace "'mirofish_sim_setup'", "'kinjeng_sim_setup'" | Set-Content "$root\frontend\src\views\SimulationView.vue"

# === FRONTEND: NavBar GitHub link ===
(Get-Content "$root\frontend\src\components\NavBar.vue") -replace 'href="https://github.com/[^"]*MiroFish[^"]*"', 'href="https://github.com/lbb-idr/KINJENG_PROJECT"' | Set-Content "$root\frontend\src\components\NavBar.vue"

# === FRONTEND: WelcomeSplash engine badge ===
(Get-Content "$root\frontend\src\components\WelcomeSplash.vue") -replace 'Engine MiroFish V1\.0', 'KINJENG Engine V1.0' | Set-Content "$root\frontend\src\components\WelcomeSplash.vue"

# === LOCALES ===
(Get-Content "$root\locales\en.json") -replace 'MiroFish-V1\.0', 'KINJENG V1.0' | Set-Content "$root\locales\en.json"
(Get-Content "$root\locales\id.json") -replace 'MiroFish V1\.0', 'KINJENG V1.0' | Set-Content "$root\locales\id.json"
(Get-Content "$root\locales\zh.json") -replace 'MiroFish-V1\.0', 'KINJENG V1.0' | Set-Content "$root\locales\zh.json"

# === BACKEND: Config default SECRET_KEY ===
(Get-Content "$root\backend\app\config.py") -replace "'mirofish-secret-key'", "'kinjeng-secret-key'" | Set-Content "$root\backend\app\config.py"

# === BACKEND: DB path (internal) — keep mirofish.db as internal filename, no visible impact ===

Write-Host "✅ Selesai membersihkan MiroFish references"
