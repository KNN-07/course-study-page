# Question craft

The page can only be as Socratic as the items you write. A deck of definition-recall questions
produces a student who recognises phrases. The aim is a student who can reason with the
material, so most items should make them **predict, explain, find a flaw, apply or connect**.

## The lesson (`reading`)

Each module page is also the student's reading material. The `reading` sections are where
the module is actually taught, in full sentences, at the length a good set of lecture notes
would use: usually 400-1200 words in three to six sections. The summary and the key-idea
cards are the recap, not the lesson.

- Teach in the order the course does, in the course's notation, from the materials. Slides
  are often bare bullet points. Your job is to restore the explanation that was spoken
  over them, using the speaker notes, the textbook readings and the worked solutions in
  the folder. Do not bring in content the course does not cover.
- Explain why, not only what. For each idea: what problem it solves, the definition, a
  concrete example worked through, then the case that trips people up.
- Put at least one fully worked example inside the text of each module.
- Write it yourself. Do not paste long passages from a textbook or paper in the folder.
  Short definitions and formulas stated as the course states them are fine.
- Use the block markup: blank lines between paragraphs, `- ` lists, `1. ` steps, `> ` for
  the one line worth boxing, fenced code. Add a `figure` where the course uses a diagram.
- End one or two sections with a `check`: a question the student answers before reading on.
  Ask for a prediction or an application of what the section just said, not a repeat of
  its last sentence. This keeps the reading active, in line with the rest of the page.
- Do not put the answers to quiz items in the lesson word for word. The lesson teaches the
  idea and the quiz tests it on a different case.

## The six kinds

Set `kind` on every quiz item. Across the quiz, keep `recall` under about a third.

| kind | The student must | Stem patterns |
|---|---|---|
| `predict` | Say what happens before being told | "What does this print?" "What happens to X if Y doubles?" |
| `explain` | Pick the right reason, not just the right fact | "Why does ...?" "Which of these explains ...?" |
| `flaw` | Locate the error in a plausible claim or solution | "A student argues ... Where does it go wrong?" |
| `apply` | Use the idea on a case not in the notes | "Given this new situation, which ...?" |
| `connect` | Relate two ideas, often from different modules | "How does X from week 2 constrain Y here?" |
| `recall` | Retrieve a fact or definition | Use sparingly, mainly at difficulty 1 |

Take the surface details of `apply` items from somewhere other than the lecture's own
example. Same numbers and names as the slide tests memory of the slide.

## Multiple choice

- One defensible answer. If a careful student could argue for two, rewrite.
- **Every wrong option is a real misconception**, the result of a specific wrong step: sign
  error, converse confusion, off-by-one, the rule from the neighbouring topic. Marking notes
  and "common mistakes" slides are the best source. No joke options, no filler.
- Options are parallel in form and similar in length. The validator flags decks where the
  right answer is usually the longest or usually in the same position.
- No "all of the above" or "none of the above".
- `why` says why the answer is right **and** names what makes the main distractor tempting.

### Probes: narrow, never tell

When the student picks a wrong option, the page shows `probes[<that option>]` and lets them
try again. A probe is the question a tutor would ask next. It should make the student
collide with their own reasoning.

- Aim at the specific misconception behind that option.
- Ask for something smaller and checkable: a definition, one row of a table, one test case.
- Never state or paraphrase the correct option. Never say which option to pick.

| Student picked | Weak probe | Good probe |
|---|---|---|
| "p → q is false when p is false" | "Remember vacuous truth." | "The promise is 'if it rains I bring an umbrella'. It stays dry. Did I break the promise?" |
| "Binary search is O(n)" | "Think about halving." | "After one comparison, how many elements can still hold the target? After two?" |
| "Demand rises when price rises" | "No, look at the curve." | "At a higher price, do you personally buy more or fewer units? What does that do along the curve?" |

Write a probe for each distractor that reflects a distinct error. Use the single `probe`
field only when all wrong options share one cause.

### Defend: devil's advocate

`defend` appears after a correct answer on some items. Give the strongest objection a smart
sceptic would raise, then the defence. Use it on items where a right answer could be luck or
pattern-matching, roughly one item in four.

## Short answer (`fill`)

This is the free-recall check: no options to recognise. One blank, one unambiguous answer.

- Ask for a term, a value, a short expression or the next line. Not a sentence.
- Fill `accept` with every reasonable spelling and notation. Test it against how you would
  type the answer yourself.
- `hint` points at the method, not the answer. Using it forfeits credit.

## Flashcards

One idea per card, answerable in a breath. Put the question on the front ("When is p → q
false?"), not a bare term. Prefer cards that ask *why* or *when* over *what is the
definition of*. Never copy a concept card word for word.

## Worked problems

Take these from problem sets and past papers where the materials include a solution. If the
materials state a problem without a solution, you may solve it, but verify the result and
say in the report that the solution is yours.

- `title` is the full problem as set.
- Each step is one move. `why` names the rule that licenses it.
- `ask` is the question shown before the step is revealed: "What can you substitute here?"
  "Which case is left?" It lets a stuck student take the smallest hint that helps.
- Include at least one problem per module whose first step is the hard part, choosing the
  method.

## Teach-back (`explain`)

One per module. The prompt asks the student to explain an idea to someone who missed the
lecture. The rubric is 3-5 points that an examiner would look for, each one checkable as
present or absent: "States the base case", not "Shows good understanding".

## Difficulty

- **1 core**: direct use of one idea. The diagnostic's easy end.
- **2 standard**: exam-typical, one or two steps.
- **3 hard**: an edge case, a boundary condition, an adversarial phrasing, or two ideas
  together. Every module needs at least one, because level 5 depends on it.

## Diagnostic

One question per module where possible, spanning difficulty 1 to 3, ordered easy to hard.
These must not teach: no leading stems, no explanations inside the question. Use different
questions from the practice pool.

## Integrative problems

One to three open problems that cannot be done with a single module. Past-paper long
questions are ideal. The rubric lists the marks: method chosen, each key step, the
conclusion. Supply a `solution`.

## Wording and tone

- Plain and exact. Use the course's notation.
- Feedback text is neutral. Write "This holds because ..." and "That would require ...".
  Do not write praise or consolation into `why`, `probes` or `defend`.
- Do not credit the student with reasoning they have not shown ("As you realised ...").

## Tutoring live

When the user pastes a `resume from:` block and wants live tutoring, the same method applies
in conversation:

1. Start from the lowest module in the map and the recorded misses.
2. Ask one question per message and end the message there. No hint, no example answer.
3. Wrong answer: ask a narrower question that exposes the contradiction. Explain directly
   only after two or three failed attempts, in a few sentences, then re-test the same idea
   from another angle.
4. Right answer: sometimes push back ("Are you sure? What about ...?") so they defend it.
5. A vague or partly right answer is not right. Keep probing.
6. Raise a level only after two independent checks, one of them unprompted. Re-test earlier
   material without warning, and lower a level on a failed review.
7. No flattery. Show the updated map when a level changes.
8. Honour "show progress", "harder", "easier", "just tell me" (this question only) and
   "save state".
