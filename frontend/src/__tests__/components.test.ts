import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { setApi } from '../api'
import { useHandoffStore } from '../stores/handoff'
import { useSessionStore } from '../stores/session'
import BriefView from '../components/BriefView.vue'
import SenderActions from '../components/SenderActions.vue'
import RolePickerView from '../views/RolePickerView.vue'
import HandoffView from '../views/HandoffView.vue'
import { detail, status } from './helpers'

beforeEach(() => { setActivePinia(createPinia()); localStorage.clear(); setApi(null) })

describe('BriefView', () => {
  it('labels AI output and highlights unfetched links', () => {
    const w = mount(BriefView, { props: { brief: detail().brief! } })
    expect(w.text()).toContain('AI-generated')
    const gaps = w.get('[data-test=gaps]').text()
    expect(gaps).toContain('Link content could not be fetched')
    expect(gaps).toContain('no tests described')
  })

  it('shows edited-by-sender instead of AI label', () => {
    const b = detail().brief!
    const w = mount(BriefView, { props: { brief: { ...b, source: 'sender' } } })
    expect(w.text()).not.toContain('AI-generated')
    expect(w.text()).toContain('Edited by sender')
  })
})

describe('RolePickerView', () => {
  it('stores the chosen role', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: RolePickerView }, { path: '/handoffs', component: { template: '<i/>' } }] })
    const w = mount(RolePickerView, { global: { plugins: [router] } })
    await w.get('[data-test=pick-receiver]').trigger('click')
    expect(useSessionStore().role).toBe('receiver')
  })
})

describe('SenderActions', () => {
  function withEvents(events: string[]) {
    const store = useHandoffStore()
    store.detail = detail({ state: 'receiver_restated', available_events: events as never })
    return store
  }
  it('offers confirm and revision when restated, but not complete', () => {
    withEvents(['confirm', 'request_revision'])
    const w = mount(SenderActions)
    expect(w.find('[data-test=confirm]').exists()).toBe(true)
    expect(w.find('[data-test=complete]').exists()).toBe(false)
  })
  it('offers complete as its own step after confirm', () => {
    withEvents(['complete'])
    const w = mount(SenderActions)
    expect(w.find('[data-test=complete]').exists()).toBe(true)
    expect(w.find('[data-test=confirm]').exists()).toBe(false)
  })
  it('requires a comment for revision', async () => {
    const store = withEvents(['confirm', 'request_revision'])
    const spy = vi.spyOn(store, 'requestRevision')
    const w = mount(SenderActions)
    await w.get('[data-test=revise]').trigger('click')
    expect(spy).not.toHaveBeenCalled()
    expect(w.text()).toContain('Explain what')
  })
  it('renders nothing when no events allow it', () => {
    withEvents([])
    expect(mount(SenderActions).find('section').exists()).toBe(false)
  })
})

describe('HandoffView', () => {
  async function render(role: 'sender' | 'receiver', d: ReturnType<typeof detail>) {
    useSessionStore().setRole(role)
    setApi({ get: vi.fn(async () => d), status: vi.fn(async () => status({ available_events: d.available_events })) } as never)
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/handoffs', component: { template: '<i/>' } }] })
    const w = mount(HandoffView, { props: { id: 1 }, global: { plugins: [router] } })
    await flushPromises()
    return w
  }

  it('receiver sees a placeholder while brief is null', async () => {
    const w = await render('receiver', detail({ state: 'ai_drafted', brief: null, available_events: [] }))
    expect(w.find('[data-test=brief-pending]').exists()).toBe(true)
    w.unmount()
  })

  it('sender can approve in ai_drafted and approve button follows available_events', async () => {
    const w = await render('sender', detail())
    expect(w.get('[data-test=approve]').attributes('disabled')).toBeUndefined()
    w.unmount()
    const w2 = await render('sender', detail({ available_events: [] }))
    expect(w2.get('[data-test=approve]').attributes('disabled')).toBeDefined()
    w2.unmount()
  })

  it('receiver can restate when allowed', async () => {
    const w = await render('receiver', detail({ state: 'sender_approved', available_events: ['restate', 'ask_question'] }))
    expect(w.find('[data-test=restate]').exists()).toBe(true)
    expect(w.find('[data-test=ask]').exists()).toBe(true)
    w.unmount()
  })

  it('sender sees retry when the draft is missing', async () => {
    const w = await render('sender', detail({ state: 'submitted', brief: null, available_events: ['draft'] }))
    expect(w.find('[data-test=draft-missing]').exists()).toBe(true)
    w.unmount()
  })
})
