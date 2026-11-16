# `course.json` schema

One JSON object. `m` is always a 0-based index into `modules`. Fields marked * are required.
Text fields accept light markup: `` `code` ``, `**bold**`, fenced code blocks, line breaks,
and `$...$` / `$$...$$` maths. Everything else is shown literally, so HTML is not needed and
not rendered.

```jsonc
{
  "course": {
    "title": "Discrete Mathematics: Logic & Proofs",  // *
    "code": "MATH 1201",              // shown above the title; omit if unknown
    "overview": "Two or three sentences on what the course covers.",
    "objectives": ["Build and read truth tables", "..."],   // "You should be able to"
    "target_level": 4,                // 1-5, level every module must reach. Default 4. Use 5 only if the user asks for full mastery
    "lang": "en",
    "accent": "#3651D4",              // optional brand colour, light theme
    "math": true                      // optional; auto-detected from $...$ if omitted
  },

  "modules": [
    {
      "title": "Propositional logic",          // *
      "short": "Propositions",                 // tag used on items, <= 22 chars
      "source": "lecture01.pptx slides 3-22",  // which files and where
      "primer": {                              // shown BEFORE the summary; student commits first
        "q": "\"If it rains, the match is off.\" It did not rain. Is the match on?",
        "a": "You cannot tell. A false hypothesis makes the implication true whatever happens."
      },
      "summary": "A proposition is ...",       // * 2-4 sentences
      "concepts": [
        { "term": "Implication", "def": "p → q is false only when ...", "example": "F → anything ≡ T" }
      ],
      "notes": [ { "heading": "Derivation", "body": "Optional longer passage." } ],
      "table": {                               // optional; use "tables": [ ... ] for more than one
        "toc": "Truth table",                  // sidebar label
        "caption": "Truth table: the five connectives",
        "headers": ["p", "q", "p → q"],
        "rows": [["T", "T", "T"], ["T", "F", "F"]]   // every row as long as headers. Cells "T"/"F" are coloured
      },
      "pitfalls": ["Treating p → q as false when p is false."],
      "sheet": [ { "k": "Implication", "v": "p → q ≡ ¬p ∨ q" } ]   // cheat-sheet lines
    }
  ],

  "diagnostic": [   // placement. One per module is ideal; span difficulty 1 to 3
    { "m": 0, "difficulty": 1, "q": "...", "options": ["...", "..."], "answer": 0, "why": "..." }
  ],

  "quiz": [
    {
      "m": 0,                         // *
      "kind": "predict",              // predict | explain | flaw | apply | connect | recall
      "difficulty": 2,                // 1 core, 2 standard, 3 hard (edge case / adversarial)
      "q": "If p is false and q is true, what is p → q?",          // *
      "options": ["True", "False", "Undefined", "Depends"],        // * 2-6
      "answer": 0,                    // * 0-based index
      "why": "A false hypothesis makes ...",                        // * shown after the item is settled
      "probes": {                     // narrower question per WRONG option, shown on the first miss
        "1": "When exactly is an implication false? Does this row match that case?",
        "2": "Does every row of a truth table have a value?"
      },
      "probe": "Fallback probe used for options without their own.",
      "defend": {                     // optional devil's-advocate challenge after a correct answer
        "q": "So \"if 2 + 2 = 5 then I am the Pope\" is true?",
        "a": "Yes. The claim is only about what follows when the hypothesis holds."
      }
    }
  ],

  "fill": [
    {
      "m": 0, "difficulty": 2,
      "prompt": "The converse of p → q is ___.",          // *
      "accept": ["q → p", "q->p", "q implies p"],          // * see matching below
      "answer": "q → p",                                   // * what is displayed as the answer
      "hint": "Swap hypothesis and conclusion.",           // revealed on request or after one miss; forfeits credit
      "probe": "Which part of the implication moves?",     // optional, shown on a miss
      "why": "Optional explanation shown with the answer."
    }
  ],

  "flashcards": [ { "m": 0, "front": "When is p → q false?", "back": "Only when p is true and q is false." } ],

  "worked": [
    {
      "m": 0, "difficulty": 2,
      "title": "Is ((p → q) ∧ p) → q a tautology?",        // * the problem statement
      "prompt": "Optional extra givens.",
      "steps": [                                           // * >= 2
        { "text": "It can only be false if ...", "why": "Implication",
          "ask": "When can an implication be false at all?" }   // shown BEFORE this step is revealed
      ]
    }
  ],

  "explain": [   // teach-back, needed for level 5
    { "m": 0, "prompt": "Explain to a classmate why a false hypothesis makes an implication true.",
      "rubric": ["States when p → q is false", "Says the claim is silent when p is false", "Gives an example"] }
  ],

  "integrative": [   // final assessment only; combine modules
    { "title": "optional", "prompt": "Prove or disprove ...", "modules": [1, 3],
      "rubric": ["Negates the statement correctly", "Chooses contrapositive", "..."],
      "solution": "Model answer shown at marking time." }
  ]
}
```

## Short-answer matching

A typed answer is lower-cased, stripped of whitespace and trailing punctuation, and `->` /
`<->` become `→` / `↔`, then compared with each `accept` entry treated the same way. Two
special forms:

- `"re:^o\\(n ?log ?n\\)$"`: a case-insensitive regular expression tested on the raw answer.
- `"num:9.81±0.01"`: a number with an optional tolerance. A decimal comma is accepted.

List the variants a student would reasonably type (symbol and word forms, with and without
units). Do not accept answers that are merely close.

## Ids and saved progress

Omit `id` and the build derives one from the item's text. Progress is keyed by id, so
rewording an item resets its history, which is usually right. Set `id` yourself only to keep
history across a rewording. The top-level `id` (course id) is derived from title and code.

## Sizing

A typical course lands at 4-10 modules and 80-200 items. The page handles far more, but more
items means a longer path to each level. Prefer better questions to more of them.
