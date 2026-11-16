# `course.json` schema

One JSON object. `m` is always a 0-based index into `modules`. Fields marked * are required.
Text fields accept light markup: `` `code` ``, `**bold**`, `*italic*`, fenced code blocks, line breaks,
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
    "exam_date": "2026-12-14",        // optional, YYYY-MM-DD. The student can set or change it on the page
    "exam_format": "2 h, closed book: 20 multiple choice, 3 long proofs",   // optional, shown on the overview
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
      "reading": [                             // the lesson: the main teaching text, 400-1200 words per module
        {
          "heading": "Why a false hypothesis makes it true",
          "body": "Paragraphs separated by blank lines.\n\n- bullet lists\n- like this\n\n1. numbered steps\n2. like this\n\n> a callout line\n\n```\ncode block\n```",
          "figure": { "src": "figs/table.png", "alt": "..." },      // optional
          "check": { "q": "Stop and answer: ...", "a": "..." }       // optional question before the next section
        }
      ],
      "concepts": [
        { "term": "Implication", "def": "p → q is false only when ...", "example": "F → anything ≡ T" }
      ],
      "notes": [ { "heading": "Derivation", "body": "Optional side passage shown as its own card." } ],
      "figures": [                             // optional diagrams for the module page. See "Figures"
        { "src": ".study/media/lecture01.pptx/slide7-1.png", "alt": "Venn diagram of p and q with the overlap shaded", "caption": "p ∧ q" }
      ],
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
      "src": "lecture01.pptx slide 9",  // where this comes from; shown after the item is settled. Also on fill and worked
      "figure": { "src": "figs/circuit3.png", "alt": "..." },   // optional; also on diagnostic, fill, worked and concepts
      "shuffle": false,               // optional; options are shuffled on every showing unless this is false
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

## Figures

A figure is `{ "src", "alt", "caption" }`. `src` is a path relative to `course.json`
(png, jpg, gif, webp or svg) and `alt` is required. The build inlines every picture into
the page, so the result is still one file. Limits: 700 KB per picture, 9 MB in total.

Where pictures come from:

- `.pptx` and `.docx`: the scan saves embedded pictures to `.study/media/<file>/slideN-K.png`
  and lists them in the outline. Use those paths directly.
- PDFs, photos, whiteboard shots: view the page with your own tools and save a crop of the
  diagram into the course folder (for example `figs/`).
- Simple diagrams you can describe exactly (a number line, a small graph, a tree) may be
  written as an `.svg` file. Redraw only what the materials show.

Use a figure when the question is about the picture ("Which region is p ∧ ¬q?") or when the
course explains the idea visually. Do not add pictures as decoration.

## Options are shuffled

The order of `options` is randomised each time a question appears, and `answer` and `probes`
keep pointing at the options as you wrote them. So write options that do not mention
letters or positions. Set `"shuffle": false` only where the order carries meaning, such as
a numeric scale.

## Ids and saved progress

Omit `id` and the build derives one from the item's text. Progress is keyed by id, so
rewording an item resets its history, which is usually right. Set `id` yourself only to keep
history across a rewording. The top-level `id` (course id) is derived from title and code.

## Sizing

A typical course lands at 4-10 modules and 80-200 items. The page handles far more, but more
items means a longer path to each level. Prefer better questions to more of them.
