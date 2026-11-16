# How the page scores, schedules and unlocks

All of this lives in `assets/template.html`. It is documented here so you can author for it
and explain it to the student.

## Credit

Every practice item keeps a record: clean checks `c`, last credited time, last time the
answer was shown, a review box and a due time.

A check earns credit only if it is **clean** and **independent**:

- clean: right on the first attempt, with no hint, no probe and no reveal in that attempt;
- independent: at least 10 minutes after the previous credited check and after the last
  time the answer was shown for that item.

So answering right immediately after reading the explanation earns nothing, and an item
becomes **secure** (`c >= 2`) only through a second clean answer after a gap. This is the
"two independent checks, one of them unprompted" rule.

Anything else (right after a probe, right with a hint, wrong, "Just tell me", revealed
worked steps) earns no credit, and the item is due again in 10 minutes. A wrong answer also
takes one check away.

| Item | Clean means |
|---|---|
| Quiz | Correct option on the first click |
| Short answer | Accepted on the first check, hint unused |
| Flashcard | Student marks "Had it" after flipping (self-rated) |
| Worked problem | Student solved on paper, then confirmed it matches, with no step revealed first |
| Teach-back | Every rubric point ticked against what they wrote |

## Module level

Core items are the module's quiz, short-answer, flashcard and worked items.

| Level | Label | Requirement |
|---|---|---|
| 0 | unaware | Nothing opened or attempted |
| 1 | heard of it | Module opened, or any item attempted |
| 2 | can follow along | 50% of core items have a clean check |
| 3 | can do with help | 80% of core items have a clean check |
| 4 | can do independently | 80% of core items secure, and a worked problem solved unaided |
| 5 | can teach it | Level 4, every difficulty-3 item secure, every teach-back complete |

The diagnostic gives a starting floor: 1 for a module tested and missed, 2 for a correct
answer, 3 for a correct hard question or a clean sweep of several. The floor never exceeds
3, because 4 and 5 need spaced evidence.

Because a miss removes a check, a failed review can drop a module a level. The page
announces every level change and redraws the map.

## Review schedule

After a credited check the item moves up a box and comes due after 10 minutes, 1 day,
3 days, 7 days, then 16 days. The review queue mixes due items from all modules in random
order, up to 20 at a time. A miss sends the item back to the first box.

### With an exam date

When an exam date is set (in `course.exam_date` or by the student), each interval is capped
at a fraction of the time remaining: 10%, 25%, 50% and 80% for the later boxes, never less
than 10 minutes. Every item therefore comes back before the exam instead of after it. The
overview shows the days left and a daily target: the number of clean answers still needed
for every item to be secure, divided by the days. With three days or fewer it advises
sitting the mock first.

## Shuffled options

Quiz and diagnostic options are shuffled each time an item is shown, so a student cannot
learn an answer by its position. Combined with the request for fresh questions on the
Progress page, this keeps "secure" from meaning "memorised this page".

## Difficulty control

- **Easier**: items of difficulty 1-2, easiest first.
- **Standard**: everything, easiest first.
- **Harder**: difficulty 2-3, hardest first, and the hint button is removed.

## Final assessment

Locked until every module is at the course's `target_level`. The paper has two questions
per module (drawn from the harder quiz and short-answer items) and up to three integrative
problems, shuffled, with no feedback until the end. Integrative answers are marked by the
student against the rubric and count as correct at 70% of points.

Pass: 80% overall and at least one correct answer in every module. Each answer also counts
as an ordinary check, so a failed final lowers the relevant items. The result lists scores
per module, the weakest areas and every missed question with its explanation.

A **mock** in the same format is available while the final is locked. It counts as evidence
per question but does not complete the course.

## Storage and portability

Progress is kept in the browser's `localStorage` under a key derived from the course id. If
storage is unavailable the page still works for the session. The Progress page offers:

- **Save state**: a code that restores everything in another browser.
- **Resume from**: paste a code.
- **Download backup file**: the same code as a file.
- **Hand-off block**: a readable summary beginning `resume from:` with the skill map and
  the recorded misses, for continuing with a live tutor.
- **More questions**: a request listing the weak modules and misses, for the agent to add
  fresh items.
- **Flagged questions**: the items the student flagged, with their notes and sources.

Flags, personal notes and the exam date are part of the saved state.

## Changing the model

The constants are at the top of the script in `assets/template.html`: `GAP` (10 minutes),
`IV` (review intervals) and the thresholds inside `evidence()`. If you change them, update
this file and the explanatory lines the page shows on the overview and Progress views.
