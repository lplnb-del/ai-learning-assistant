<script setup lang="ts">
import { Database, MousePointerClick, Plus } from '@lucide/vue'
import { decks, flashCard } from '../../mock/workspace'
</script>

<template>
  <section class="cards-view" aria-label="QA 记忆卡片">
    <aside class="resource-sidebar cards-sidebar">
      <header><span>我的卡组</span><button type="button" aria-label="新建卡组"><Plus :size="16" /></button></header>
      <button v-for="deck in decks" :key="deck.id" class="resource-nav-button" :class="{ 'resource-nav-active': deck.active }" type="button">
        <component :is="deck.icon" :size="17" />
        <span>{{ deck.label }}</span>
        <code>{{ deck.count }}</code>
      </button>
    </aside>

    <main class="review-stage">
      <header>
        <span>正在复习: 1 / 42</span>
        <button type="button">退出复习</button>
      </header>

      <div class="flashcard">
        <div class="flashcard-front">
          <div class="flashcard-meta">
            <span># {{ flashCard.tag }}</span>
            <span><Database :size="13" />关联知识库</span>
          </div>
          <h2>{{ flashCard.question }}</h2>
          <p><MousePointerClick :size="16" />点击翻转查看答案</p>
        </div>
        <div class="flashcard-back">
          <h3>参考答案</h3>
          <p v-for="line in flashCard.answer" :key="line">{{ line }}</p>
        </div>
      </div>

      <div class="memory-actions">
        <button class="score-red" type="button"><strong>重来</strong><span>&lt; 1 min</span></button>
        <button class="score-yellow" type="button"><strong>模糊</strong><span>10 min</span></button>
        <button class="score-green" type="button"><strong>掌握</strong><span>1 day</span></button>
      </div>
    </main>
  </section>
</template>
