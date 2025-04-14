## Experiments & Abandoned Approaches

The `experiments/` folder contains early explorations and prototype ideas that were investigated but ultimately **not used** in the final system. While these are not production solutions, we document them here for transparency and to avoid future repetition.

### 1. Medical BERT Similarity Analysis

We evaluated multiple pretrained **Medical BERT** models by comparing similarity scores across various medical relation types:

- **Relation Types Tested**:
  - Synonymy
  - Hypernymy
  - Causal
  - Has-a
  - Comorbidity
  - Treatment
  - Part-Whole
  - Random
  - Opposites
  - Related Symptoms
  - Lexically Similar Words

- **Key Insight**:
  Despite expectations, **Random** and **Opposites** had *high similarity scores*, while **Synonyms** and **Causal** pairs had *low similarity scores*. This indicated poor alignment of semantic similarity scores with actual clinical meaning, and made this method unreliable for downstream classification.

---

### 2. Category Generator via Hyde AI

We explored a **Hyde AI-inspired mechanism** to enrich input data by generating associated concepts for each observation title, such as:

- Likely **medications**
- Relevant **observations/symptoms**
- Associated **disorders**

The goal was to give the LLM richer context to improve inference about patient conditions.

- **Why It Was Abandoned**:
  While conceptually useful, this method suffered from:
  - High risk of **misclassification**
  - Poor understanding of **interactions between features** (e.g., how combining a medication and a symptom changes the meaning)
  - Incorrect assumptions made by the LLM due to lack of true clinical reasoning

---

These experimental paths were essential in shaping our final approach, even though they are not part of the final deployed pipeline.
