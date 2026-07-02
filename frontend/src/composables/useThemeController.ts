import { computed, onMounted, onUnmounted, shallowRef, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { usePreferencesStore } from '../stores/preferences'

export function useThemeController() {
  const preferences = usePreferencesStore()
  const { themeMode } = storeToRefs(preferences)
  const prefersDark = shallowRef(false)

  let mediaQuery: MediaQueryList | null = null

  const resolvedTheme = computed(() => {
    if (themeMode.value === 'system') {
      return prefersDark.value ? 'dark' : 'light'
    }

    return themeMode.value
  })

  function applyTheme() {
    document.documentElement.dataset.theme = resolvedTheme.value
    document.documentElement.classList.toggle('dark', resolvedTheme.value === 'dark')
  }

  function toggleTheme() {
    preferences.setThemeMode(resolvedTheme.value === 'dark' ? 'light' : 'dark')
  }

  function handleSystemThemeChange(event: MediaQueryListEvent) {
    prefersDark.value = event.matches
  }

  onMounted(() => {
    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    prefersDark.value = mediaQuery.matches
    mediaQuery.addEventListener('change', handleSystemThemeChange)
    applyTheme()
  })

  onUnmounted(() => {
    mediaQuery?.removeEventListener('change', handleSystemThemeChange)
  })

  watch(resolvedTheme, applyTheme)

  return {
    resolvedTheme,
    toggleTheme,
  }
}
