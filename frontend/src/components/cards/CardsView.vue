<script setup lang="ts">
import CardsCreatePanel from './CardsCreatePanel.vue'
import CardsLibrarySidebar from './CardsLibrarySidebar.vue'
import CardsReviewStage from './CardsReviewStage.vue'
import { useCardsManager } from '../../composables/useCardsManager'

const cards = useCardsManager()
</script>

<template>
  <section class="cards-view" aria-label="QA 记忆卡片">
    <CardsLibrarySidebar
      :libraries="cards.qaLibraries.value"
      :selected-library-id="cards.selectedLibraryId.value"
      :library-name-draft="cards.libraryNameDraft.value"
      :library-description-draft="cards.libraryDescriptionDraft.value"
      :is-loading="cards.isLoading.value"
      :is-saving="cards.isSaving.value"
      :can-create-library="cards.canCreateLibrary.value"
      @select-library="cards.selectLibrary"
      @update-library-name-draft="cards.libraryNameDraft.value = $event"
      @update-library-description-draft="cards.libraryDescriptionDraft.value = $event"
      @create-library="cards.createLibrary"
      @remove-selected-library="cards.removeSelectedLibrary"
      @refresh="cards.applyFilters"
    />

    <CardsReviewStage
      :selected-library="cards.selectedLibrary.value"
      :cards="cards.cards.value"
      :selected-card="cards.selectedCard.value"
      :selected-card-id="cards.selectedCardId.value"
      :selected-knowledge-base-id="cards.selectedKnowledgeBaseId.value"
      :selected-mastery="cards.selectedMastery.value"
      :tag-filter="cards.tagFilter.value"
      :card-position="cards.cardPosition.value"
      :is-flipped="cards.isFlipped.value"
      :is-saving="cards.isSaving.value"
      :error-message="cards.errorMessage.value"
      :success-message="cards.successMessage.value"
      :knowledge-bases="cards.knowledgeBases.value"
      @update-selected-knowledge-base-id="cards.selectedKnowledgeBaseId.value = $event"
      @update-selected-mastery="cards.selectedMastery.value = $event"
      @update-tag-filter="cards.tagFilter.value = $event"
      @apply-filters="cards.applyFilters"
      @select-card="cards.selectCard"
      @toggle-flip="cards.toggleFlip"
      @remove-selected-card="cards.removeSelectedCard"
      @set-mastery="cards.setMastery"
    />

    <CardsCreatePanel
      :selected-library="cards.selectedLibrary.value"
      :question-draft="cards.questionDraft.value"
      :answer-draft="cards.answerDraft.value"
      :tags-draft="cards.tagsDraft.value"
      :card-knowledge-base-id-draft="cards.cardKnowledgeBaseIdDraft.value"
      :knowledge-bases="cards.knowledgeBases.value"
      :can-create-card="cards.canCreateCard.value"
      @update-question-draft="cards.questionDraft.value = $event"
      @update-answer-draft="cards.answerDraft.value = $event"
      @update-tags-draft="cards.tagsDraft.value = $event"
      @update-card-knowledge-base-id-draft="cards.cardKnowledgeBaseIdDraft.value = $event"
      @create-manual-card="cards.createManualCard"
    />
  </section>
</template>
