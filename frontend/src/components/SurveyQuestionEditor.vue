<template>
  <div class="editor-container">
    <div class="editor-header">
      <h2 class="editor-title">✏️ Edit Pertanyaan Survei</h2>
      <p class="editor-desc">Sesuaikan pertanyaan sesuai kebutuhan Anda. Tambah, hapus, atau ubah urutan pertanyaan.</p>
    </div>

    <!-- Judul & Deskripsi Survei -->
    <div class="survey-meta">
      <div class="field-group">
        <label>Judul Survei</label>
        <input v-model="localSurvey.title" class="field-input" />
      </div>
      <div class="field-group">
        <label>Deskripsi Survei</label>
        <textarea v-model="localSurvey.description" class="field-textarea" rows="2"></textarea>
      </div>
      <div class="field-group">
        <label>Skala Likert</label>
        <select v-model.number="localSurvey.params.likertScale" class="field-select">
          <option :value="5">5-point</option>
          <option :value="7">7-point</option>
        </select>
      </div>
    </div>

    <!-- Sections -->
    <div v-for="(section, sIdx) in localSurvey.sections" :key="section.id" class="section-card">
      <div class="section-header">
        <div class="section-title-row">
          <input v-model="section.title" class="section-title-input" :placeholder="`Bagian ${sIdx + 1}`" />
          <div class="section-actions">
            <button class="btn-move" @click="moveSection(sIdx, -1)" :disabled="sIdx === 0" title="Naik">↑</button>
            <button class="btn-move" @click="moveSection(sIdx, 1)" :disabled="sIdx === localSurvey.sections.length - 1" title="Turun">↓</button>
            <button class="btn-danger-sm" @click="removeSection(sIdx)" title="Hapus bagian">✕</button>
          </div>
        </div>
        <textarea v-model="section.description" class="section-desc-input" placeholder="Deskripsi bagian (opsional)" rows="1"></textarea>
      </div>

      <!-- Questions in section -->
      <div v-for="(q, qIdx) in section.questions" :key="q.id" class="question-card">
        <div class="q-header">
          <span class="q-number">Pertanyaan {{ qIdx + 1 }}</span>
          <div class="q-actions">
            <button class="btn-move" @click="moveQuestion(sIdx, qIdx, -1)" :disabled="qIdx === 0" title="Naik">↑</button>
            <button class="btn-move" @click="moveQuestion(sIdx, qIdx, 1)" :disabled="qIdx === section.questions.length - 1" title="Turun">↓</button>
            <button class="btn-danger-sm" @click="removeQuestion(sIdx, qIdx)" title="Hapus pertanyaan">✕</button>
          </div>
        </div>

        <div class="q-body">
          <div class="q-field-row">
            <div class="q-field flex-1">
              <label>Teks Pertanyaan</label>
              <textarea v-model="q.text" class="q-textarea" rows="2" :placeholder="`Tulis pertanyaan ${qIdx + 1}...`"></textarea>
            </div>
            <div class="q-field q-type-field">
              <label>Tipe</label>
              <select v-model="q.type" class="field-select" @change="onTypeChange(q)">
                <option value="likert">Likert</option>
                <option value="mcq">Pilihan Ganda</option>
                <option value="open">Esai</option>
              </select>
            </div>
          </div>

          <!-- Likert options -->
          <div v-if="q.type === 'likert'" class="q-options">
            <div class="likert-labels">
              <div class="label-row" v-for="(label, lIdx) in computedLabels(q)" :key="lIdx">
                <span class="label-num">{{ lIdx + 1 }}</span>
                <input v-model="computedLabels(q)[lIdx]" class="label-input" :placeholder="`Label ${lIdx + 1}`" />
              </div>
            </div>
          </div>

          <!-- MCQ options -->
          <div v-if="q.type === 'mcq'" class="q-options">
            <div class="option-row" v-for="(opt, oIdx) in q.options" :key="oIdx">
              <input v-model="q.options[oIdx]" class="option-input" :placeholder="`Opsi ${oIdx + 1}`" />
              <button class="btn-remove-opt" @click="removeOption(sIdx, qIdx, oIdx)" v-if="q.options.length > 2">✕</button>
            </div>
            <button class="btn-add-opt" @click="addOption(sIdx, qIdx)">+ Tambah Opsi</button>
          </div>

          <div class="q-required">
            <label class="checkbox-label">
              <input type="checkbox" v-model="q.required" />
              Wajib diisi
            </label>
          </div>
        </div>
      </div>

      <button class="btn-add-question" @click="addQuestion(sIdx)">+ Tambah Pertanyaan</button>
    </div>

    <button class="btn-add-section" @click="addSection">+ Tambah Bagian</button>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  survey: { type: Object, required: true }
})

const emit = defineEmits(['update:survey'])

const defaultLabels5 = ['Sangat Tidak Setuju', 'Tidak Setuju', 'Netral', 'Setuju', 'Sangat Setuju']
const defaultLabels7 = ['Sangat Tidak Setuju', 'Tidak Setuju', 'Agak Tidak Setuju', 'Netral', 'Agak Setuju', 'Setuju', 'Sangat Setuju']

function cloneSurvey(survey) {
  return JSON.parse(JSON.stringify(survey))
}

const genId = () => 'q_' + Math.random().toString(36).slice(2, 8)

const localSurvey = ref(cloneSurvey(props.survey))

watch(localSurvey, () => {
  emit('update:survey', cloneSurvey(localSurvey.value))
}, { deep: true })

function computedLabels(q) {
  if (q.type !== 'likert') return []
  const scale = localSurvey.value.params?.likertScale || 5
  if (!q.labels || q.labels.length !== scale) {
    q.labels = scale === 5 ? [...defaultLabels5] : [...defaultLabels7]
  }
  return q.labels
}

function defaultQuestion(type) {
  const scale = localSurvey.value.params?.likertScale || 5
  const q = {
    id: genId(),
    text: '',
    type: type || 'likert',
    required: true
  }
  if (q.type === 'likert') {
    q.scale = Array.from({ length: scale }, (_, i) => i + 1)
    q.labels = scale === 5 ? [...defaultLabels5] : [...defaultLabels7]
  } else if (q.type === 'mcq') {
    q.options = ['Opsi A', 'Opsi B', 'Opsi C']
  }
  return q
}

function onTypeChange(q) {
  if (q.type === 'likert') {
    const scale = localSurvey.value.params?.likertScale || 5
    q.scale = Array.from({ length: scale }, (_, i) => i + 1)
    q.labels = scale === 5 ? [...defaultLabels5] : [...defaultLabels7]
    delete q.options
  } else if (q.type === 'mcq') {
    q.options = ['Opsi A', 'Opsi B', 'Opsi C']
    delete q.scale
    delete q.labels
  } else {
    delete q.scale
    delete q.labels
    delete q.options
  }
}

function addQuestion(sIdx) {
  localSurvey.value.sections[sIdx].questions.push(defaultQuestion('likert'))
}

function removeQuestion(sIdx, qIdx) {
  localSurvey.value.sections[sIdx].questions.splice(qIdx, 1)
}

function moveQuestion(sIdx, qIdx, dir) {
  const qs = localSurvey.value.sections[sIdx].questions
  const target = qIdx + dir
  if (target < 0 || target >= qs.length) return
  const temp = qs[qIdx]
  qs[qIdx] = qs[target]
  qs[target] = temp
}

function addOption(sIdx, qIdx) {
  const q = localSurvey.value.sections[sIdx].questions[qIdx]
  q.options.push(`Opsi ${q.options.length + 1}`)
}

function removeOption(sIdx, qIdx, oIdx) {
  localSurvey.value.sections[sIdx].questions[qIdx].options.splice(oIdx, 1)
}

function addSection() {
  const sIdx = localSurvey.value.sections.length
  localSurvey.value.sections.push({
    id: `section_${sIdx + 1}`,
    title: `Bagian ${sIdx + 1}`,
    description: '',
    questions: [defaultQuestion('likert')]
  })
}

function removeSection(sIdx) {
  localSurvey.value.sections.splice(sIdx, 1)
}

function moveSection(sIdx, dir) {
  const sections = localSurvey.value.sections
  const target = sIdx + dir
  if (target < 0 || target >= sections.length) return
  const temp = sections[sIdx]
  sections[sIdx] = sections[target]
  sections[target] = temp
}

defineExpose({ getSurvey: () => cloneSurvey(localSurvey.value) })
</script>

<style scoped>
.editor-container {
  border: 2px solid var(--accent-primary, #3B82F6);
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  background: var(--bg-card, #FFF);
}
.editor-header { margin-bottom: 20px; }
.editor-title { font-size: 1.3rem; font-weight: 700; margin: 0 0 6px; }
.editor-desc { font-size: 0.9rem; color: var(--text-secondary, #6B7280); margin: 0; }

.survey-meta { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 20px; padding: 16px; background: var(--bg-secondary, #F9FAFB); border-radius: 6px; }
.field-group { flex: 1; min-width: 200px; }
.field-group label { display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 4px; color: var(--text-secondary, #6B7280); text-transform: uppercase; letter-spacing: 0.5px; }
.field-input, .field-select, .field-textarea { width: 100%; padding: 8px 10px; border: 1px solid var(--border-color, #D1D5DB); border-radius: 4px; font-size: 0.9rem; background: var(--bg-primary, #FFF); color: var(--text-primary, #1F2937); }
.field-textarea { resize: vertical; font-family: inherit; }
.field-input:focus, .field-select:focus, .field-textarea:focus { outline: none; border-color: var(--accent-primary, #3B82F6); }

.section-card { border: 1px solid var(--border-color, #E5E7EB); border-radius: 6px; margin-bottom: 16px; background: var(--bg-primary, #FFF); }
.section-header { padding: 12px 16px; border-bottom: 1px solid var(--border-color, #E5E7EB); background: var(--bg-secondary, #F9FAFB); border-radius: 6px 6px 0 0; }
.section-title-row { display: flex; align-items: center; gap: 8px; }
.section-title-input { flex: 1; font-size: 1rem; font-weight: 600; padding: 6px 8px; border: 1px solid transparent; border-radius: 4px; background: transparent; color: var(--text-primary, #1F2937); }
.section-title-input:focus { border-color: var(--accent-primary, #3B82F6); background: var(--bg-primary, #FFF); outline: none; }
.section-actions { display: flex; gap: 4px; }
.section-desc-input { width: 100%; margin-top: 8px; padding: 6px 8px; border: 1px solid transparent; border-radius: 4px; font-size: 0.85rem; background: transparent; color: var(--text-secondary, #6B7280); resize: vertical; font-family: inherit; }
.section-desc-input:focus { border-color: var(--accent-primary, #3B82F6); background: var(--bg-primary, #FFF); outline: none; }

.question-card { margin: 8px 12px; border: 1px solid var(--border-color, #E5E7EB); border-radius: 6px; overflow: hidden; }
.q-header { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: var(--bg-secondary, #F9FAFB); border-bottom: 1px solid var(--border-color, #E5E7EB); }
.q-number { font-size: 0.8rem; font-weight: 600; color: var(--text-secondary, #6B7280); font-family: var(--font-mono, monospace); }
.q-actions { display: flex; gap: 4px; }
.q-body { padding: 12px; }
.q-field-row { display: flex; gap: 12px; }
.q-field { margin-bottom: 10px; }
.q-field label { display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 4px; color: var(--text-secondary, #6B7280); text-transform: uppercase; letter-spacing: 0.5px; }
.flex-1 { flex: 1; }
.q-type-field { min-width: 140px; }
.q-textarea { width: 100%; padding: 8px 10px; border: 1px solid var(--border-color, #D1D5DB); border-radius: 4px; font-size: 0.9rem; resize: vertical; background: var(--bg-primary, #FFF); color: var(--text-primary, #1F2937); font-family: inherit; }
.q-textarea:focus { outline: none; border-color: var(--accent-primary, #3B82F6); }

.q-options { padding: 8px 0; }
.likert-labels { display: flex; flex-wrap: wrap; gap: 6px; }
.label-row { display: flex; align-items: center; gap: 4px; }
.label-num { font-size: 0.75rem; font-weight: 700; color: var(--text-secondary, #6B7280); min-width: 16px; text-align: center; font-family: var(--font-mono, monospace); }
.label-input { width: 120px; padding: 4px 6px; border: 1px solid var(--border-color, #D1D5DB); border-radius: 3px; font-size: 0.8rem; background: var(--bg-primary, #FFF); color: var(--text-primary, #1F2937); }
.label-input:focus { outline: none; border-color: var(--accent-primary, #3B82F6); }

.option-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.option-input { flex: 1; max-width: 300px; padding: 6px 8px; border: 1px solid var(--border-color, #D1D5DB); border-radius: 4px; font-size: 0.85rem; background: var(--bg-primary, #FFF); color: var(--text-primary, #1F2937); }
.option-input:focus { outline: none; border-color: var(--accent-primary, #3B82F6); }
.btn-remove-opt { background: none; border: none; color: #EF4444; cursor: pointer; font-size: 1rem; padding: 2px 4px; }
.btn-add-opt { background: none; border: 1px dashed var(--border-color, #D1D5DB); padding: 6px 16px; border-radius: 4px; font-size: 0.8rem; cursor: pointer; color: var(--text-secondary, #6B7280); margin-top: 4px; }
.btn-add-opt:hover { border-color: var(--accent-primary, #3B82F6); color: var(--accent-primary, #3B82F6); }

.q-required { margin-top: 8px; }
.checkbox-label { display: flex; align-items: center; gap: 6px; font-size: 0.85rem; color: var(--text-secondary, #6B7280); cursor: pointer; }

.btn-move { background: none; border: 1px solid var(--border-color, #D1D5DB); border-radius: 3px; padding: 2px 8px; cursor: pointer; font-size: 0.85rem; color: var(--text-secondary, #6B7280); }
.btn-move:hover:not(:disabled) { border-color: var(--accent-primary, #3B82F6); color: var(--accent-primary, #3B82F6); }
.btn-move:disabled { opacity: 0.3; cursor: not-allowed; }
.btn-danger-sm { background: none; border: none; color: #9CA3AF; cursor: pointer; font-size: 1rem; padding: 2px 6px; }
.btn-danger-sm:hover { color: #EF4444; }

.btn-add-question { width: 100%; padding: 10px; border: 2px dashed var(--border-color, #D1D5DB); background: none; border-radius: 0 0 6px 6px; font-size: 0.9rem; cursor: pointer; color: var(--text-secondary, #6B7280); font-family: inherit; }
.btn-add-question:hover { border-color: var(--accent-primary, #3B82F6); color: var(--accent-primary, #3B82F6); background: var(--bg-secondary, #F9FAFB); }
.btn-add-section { width: 100%; padding: 14px; border: 2px dashed var(--accent-primary, #3B82F6); background: none; border-radius: 6px; font-size: 1rem; cursor: pointer; color: var(--accent-primary, #3B82F6); font-weight: 600; font-family: inherit; }
.btn-add-section:hover { background: var(--bg-secondary, #F9FAFB); }
</style>
