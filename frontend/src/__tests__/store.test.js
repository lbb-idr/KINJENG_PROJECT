import { describe, it, expect, beforeEach } from 'vitest'
import state, {
  setPendingUpload,
  getPendingUpload,
  clearPendingUpload,
  clearAll,
  setSimulationType,
} from '@/store/pendingUpload'

describe('pendingUpload store', () => {
  beforeEach(() => {
    clearAll()
  })

  it('starts with default state', () => {
    const s = getPendingUpload()
    expect(s.files).toEqual([])
    expect(s.simulationRequirement).toBe('')
    expect(s.isPending).toBe(false)
    expect(s.simulationType).toBeNull()
    expect(s.surveyParams).toEqual({
      agentCount: 500,
      maxRounds: 10,
      platform: 'both',
      likertScale: 5,
    })
  })

  it('setPendingUpload sets files and requirement', () => {
    setPendingUpload(['file1.pdf', 'file2.txt'], 'Test requirement')
    const s = getPendingUpload()
    expect(s.files).toEqual(['file1.pdf', 'file2.txt'])
    expect(s.simulationRequirement).toBe('Test requirement')
    expect(s.isPending).toBe(true)
  })

  it('clearPendingUpload resets files/requirement but keeps simulationType and surveyParams', () => {
    setSimulationType('academic', { maxRounds: 20 })
    setPendingUpload(['doc.pdf'], 'req')

    clearPendingUpload()

    const s = getPendingUpload()
    expect(s.files).toEqual([])
    expect(s.simulationRequirement).toBe('')
    expect(s.isPending).toBe(false)
    expect(s.simulationType).toBe('academic')
    expect(s.surveyParams.maxRounds).toBe(20)
  })

  it('clearAll resets everything including simulationType and surveyParams', () => {
    setSimulationType('political', { agentCount: 100 })
    setPendingUpload(['doc.pdf'], 'req')
    clearAll()

    const s = getPendingUpload()
    expect(s.files).toEqual([])
    expect(s.isPending).toBe(false)
    expect(s.simulationType).toBeNull()
    expect(s.surveyParams.agentCount).toBe(500)
    expect(s.surveyParams.maxRounds).toBe(10)
  })

  it('setSimulationType sets type and merges params', () => {
    setSimulationType('market', { agentCount: 1000, platform: 'twitter' })
    const s = getPendingUpload()
    expect(s.simulationType).toBe('market')
    expect(s.surveyParams.agentCount).toBe(1000)
    expect(s.surveyParams.platform).toBe('twitter')
    expect(s.surveyParams.maxRounds).toBe(10)
  })

  it('setSimulationType works with no params', () => {
    setSimulationType('custom')
    const s = getPendingUpload()
    expect(s.simulationType).toBe('custom')
    expect(s.surveyParams).toEqual({
      agentCount: 500,
      maxRounds: 10,
      platform: 'both',
      likertScale: 5,
    })
  })

  it('getPendingUpload returns a copy of surveyParams', () => {
    setSimulationType('academic', { agentCount: 300 })
    const s1 = getPendingUpload()
    const s2 = getPendingUpload()
    expect(s1.surveyParams).toEqual(s2.surveyParams)
    s1.surveyParams.agentCount = 999
    expect(s2.surveyParams.agentCount).toBe(300)
  })

  it('state is reactive', () => {
    setPendingUpload(['test.pdf'], 'my requirement')
    expect(state.files).toEqual(['test.pdf'])
    expect(state.simulationRequirement).toBe('my requirement')
    expect(state.isPending).toBe(true)
  })
})
