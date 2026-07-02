import { defineStore } from 'pinia'
import { shallowRef } from 'vue'

export type ThemeMode = 'system' | 'light' | 'dark'

export const usePreferencesStore = defineStore('preferences', () => {
  const themeMode = shallowRef<ThemeMode>('system')

  function setThemeMode(nextMode: ThemeMode) {
    themeMode.value = nextMode
  }

  return {
    themeMode,
    setThemeMode,
  }
})
