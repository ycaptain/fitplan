# FitPlan AI — offline evaluation report

Seed 42; scenarios generated from `backend/tests/fixtures/sample_plans.json`.

## Initial-plan generators

| split | n | algorithm | total | recovery | conflicts | nodes | ms |
|---|---|---|---|---|---|---|---|
| ppl | 3 | csp_bt_fc | 0.0 | 0.0 | 0 | 3 | 0 |
| ppl | 3 | beam_search | 0.0 | 0.0 | 0 | 294 | 2 |
| ppl | 3 | greedy_baseline | -4.0 | 0.0 | 0 | 6 | 0 |
| ppl | 3 | ga_generate | 0.0 | 0.0 | 0 | 800 | 17 |
| ppl | 5 | csp_bt_fc | 2.0 | 2.0 | 0 | 5 | 0 |
| ppl | 5 | beam_search | 2.0 | 2.0 | 0 | 546 | 3 |
| ppl | 5 | greedy_baseline | -10.0 | -2.0 | 0 | 15 | 0 |
| ppl | 5 | ga_generate | 2.0 | 2.0 | 0 | 800 | 26 |
| upper_lower | 3 | csp_bt_fc | 1.0 | 1.0 | 0 | 3 | 0 |
| upper_lower | 3 | beam_search | 1.0 | 1.0 | 0 | 294 | 2 |
| upper_lower | 3 | greedy_baseline | -5.0 | -1.0 | 0 | 6 | 0 |
| upper_lower | 3 | ga_generate | 1.0 | 1.0 | 0 | 800 | 18 |
| upper_lower | 5 | csp_bt_fc | 4.0 | 4.0 | 0 | 5 | 0 |
| upper_lower | 5 | beam_search | 4.0 | 4.0 | 0 | 546 | 3 |
| upper_lower | 5 | greedy_baseline | -12.0 | -4.0 | 0 | 16 | 0 |
| upper_lower | 5 | ga_generate | 4.0 | 4.0 | 0 | 800 | 28 |
| full_body | 3 | csp_bt_fc | 3.0 | 3.0 | 0 | 3 | 0 |
| full_body | 3 | beam_search | 3.0 | 3.0 | 0 | 294 | 2 |
| full_body | 3 | greedy_baseline | -7.0 | -3.0 | 0 | 6 | 0 |
| full_body | 3 | ga_generate | 3.0 | 3.0 | 0 | 800 | 20 |
| full_body | 5 | csp_bt_fc | 6.0 | 6.0 | 0 | 135 | 0 |
| full_body | 5 | beam_search | 3.0 | 3.0 | 0 | 420 | 2 |
| full_body | 5 | greedy_baseline | -18.0 | -10.0 | 0 | 15 | 0 |
| full_body | 5 | ga_generate | 6.0 | 6.0 | 0 | 800 | 33 |

## Replanners across 36 disturbance scenarios

| scenario | intensity | algorithm | hard before→after | score delta | moved | ms |
|---|---|---|---|---|---|---|
| ppl-base-001/fixed-event/single-slot | 0.17 | hill_climbing | 1→0 | +0.0 | 1 | 6.7 |
| ppl-base-001/fixed-event/single-slot | 0.17 | simulated_annealing | 1→0 | +0.0 | 1 | 9.0 |
| ppl-base-001/fixed-event/evening-block | 0.17 | hill_climbing | 1→0 | +0.0 | 1 | 7.8 |
| ppl-base-001/fixed-event/evening-block | 0.17 | simulated_annealing | 1→0 | +0.0 | 1 | 8.9 |
| ppl-base-001/fixed-event/full-day | 0.17 | hill_climbing | 1→0 | +0.0 | 1 | 6.7 |
| ppl-base-001/fixed-event/full-day | 0.17 | simulated_annealing | 1→0 | +0.0 | 1 | 9.0 |
| ppl-base-001/fixed-event/every-training-day | 1.00 | hill_climbing | 6→0 | +0.0 | 6 | 110.3 |
| ppl-base-001/fixed-event/every-training-day | 1.00 | simulated_annealing | 6→0 | +0.0 | 6 | 9.6 |
| ppl-base-001/missed/session-0 | 0.17 | hill_climbing | 0→0 | +0.0 | 1 | 4.6 |
| ppl-base-001/missed/session-0 | 0.17 | simulated_annealing | 0→0 | +0.0 | 0 | 8.5 |
| ppl-base-001/missed/session-3 | 0.17 | hill_climbing | 0→0 | +0.0 | 1 | 4.6 |
| ppl-base-001/missed/session-3 | 0.17 | simulated_annealing | 0→0 | +0.0 | 0 | 8.5 |
| ppl-base-001/missed/session-5 | 0.17 | hill_climbing | 0→0 | +0.0 | 1 | 4.7 |
| ppl-base-001/missed/session-5 | 0.17 | simulated_annealing | 0→0 | +0.0 | 0 | 8.4 |
| ppl-base-001/state/recovered | 0.00 | hill_climbing | 0→0 | +0.0 | 0 | 0.1 |
| ppl-base-001/state/recovered | 0.00 | simulated_annealing | 0→0 | +0.0 | 0 | 0.1 |
| ppl-base-001/state/high-fatigue | 0.17 | hill_climbing | 0→0 | +0.0 | 1 | 4.7 |
| ppl-base-001/state/high-fatigue | 0.17 | simulated_annealing | 0→0 | +0.0 | 0 | 8.7 |
| ppl-base-001/state/low-sleep | 0.17 | hill_climbing | 0→0 | +0.0 | 1 | 4.5 |
| ppl-base-001/state/low-sleep | 0.17 | simulated_annealing | 0→0 | +0.0 | 0 | 8.3 |
| ppl-base-001/manual/to-free-slot | 0.17 | hill_climbing | 0→0 | +0.0 | 1 | 4.8 |
| ppl-base-001/manual/to-free-slot | 0.17 | simulated_annealing | 0→0 | +0.0 | 0 | 8.5 |
| ppl-base-001/manual/onto-other-session | 0.17 | hill_climbing | 0→0 | +0.0 | 1 | 4.9 |
| ppl-base-001/manual/onto-other-session | 0.17 | simulated_annealing | 0→0 | +0.0 | 0 | 8.4 |
| ul-base-001/fixed-event/single-slot | 0.25 | hill_climbing | 1→0 | +0.0 | 1 | 5.7 |
| ul-base-001/fixed-event/single-slot | 0.25 | simulated_annealing | 1→0 | +0.0 | 1 | 6.5 |
| ul-base-001/fixed-event/evening-block | 0.25 | hill_climbing | 1→0 | +0.0 | 1 | 5.7 |
| ul-base-001/fixed-event/evening-block | 0.25 | simulated_annealing | 1→0 | +0.0 | 1 | 6.3 |
| ul-base-001/fixed-event/full-day | 0.25 | hill_climbing | 1→0 | +0.0 | 1 | 4.6 |
| ul-base-001/fixed-event/full-day | 0.25 | simulated_annealing | 1→0 | +0.0 | 1 | 6.2 |
| ul-base-001/fixed-event/every-training-day | 1.00 | hill_climbing | 4→0 | +0.0 | 4 | 42.3 |
| ul-base-001/fixed-event/every-training-day | 1.00 | simulated_annealing | 4→0 | +0.0 | 4 | 6.6 |
| ul-base-001/missed/session-0 | 0.25 | hill_climbing | 0→0 | +0.0 | 1 | 3.4 |
| ul-base-001/missed/session-0 | 0.25 | simulated_annealing | 0→0 | +0.0 | 0 | 6.3 |
| ul-base-001/missed/session-2 | 0.25 | hill_climbing | 0→0 | +0.0 | 1 | 3.4 |
| ul-base-001/missed/session-2 | 0.25 | simulated_annealing | 0→0 | +0.0 | 0 | 6.2 |
| ul-base-001/missed/session-3 | 0.25 | hill_climbing | 0→0 | +0.0 | 1 | 3.3 |
| ul-base-001/missed/session-3 | 0.25 | simulated_annealing | 0→0 | +0.0 | 0 | 6.1 |
| ul-base-001/state/recovered | 0.00 | hill_climbing | 0→0 | +0.0 | 0 | 0.1 |
| ul-base-001/state/recovered | 0.00 | simulated_annealing | 0→0 | +0.0 | 0 | 0.1 |
| ul-base-001/state/high-fatigue | 0.25 | hill_climbing | 0→0 | +0.0 | 1 | 3.5 |
| ul-base-001/state/high-fatigue | 0.25 | simulated_annealing | 0→0 | +0.0 | 0 | 6.1 |
| ul-base-001/state/low-sleep | 0.25 | hill_climbing | 0→0 | +0.0 | 1 | 3.5 |
| ul-base-001/state/low-sleep | 0.25 | simulated_annealing | 0→0 | +0.0 | 0 | 6.1 |
| ul-base-001/manual/to-free-slot | 0.25 | hill_climbing | 0→0 | +0.0 | 1 | 3.4 |
| ul-base-001/manual/to-free-slot | 0.25 | simulated_annealing | 0→0 | +0.0 | 0 | 6.0 |
| ul-base-001/manual/onto-other-session | 0.25 | hill_climbing | 0→0 | +0.0 | 1 | 3.3 |
| ul-base-001/manual/onto-other-session | 0.25 | simulated_annealing | 0→0 | +0.0 | 0 | 6.2 |
| fb-base-001/fixed-event/single-slot | 0.33 | hill_climbing | 1→0 | +0.0 | 1 | 5.2 |
| fb-base-001/fixed-event/single-slot | 0.33 | simulated_annealing | 1→0 | +0.0 | 1 | 5.2 |
| fb-base-001/fixed-event/evening-block | 0.33 | hill_climbing | 1→0 | +0.0 | 1 | 4.3 |
| fb-base-001/fixed-event/evening-block | 0.33 | simulated_annealing | 1→0 | +0.0 | 1 | 5.0 |
| fb-base-001/fixed-event/full-day | 0.33 | hill_climbing | 1→0 | +0.0 | 1 | 4.5 |
| fb-base-001/fixed-event/full-day | 0.33 | simulated_annealing | 1→0 | +0.0 | 1 | 5.4 |
| fb-base-001/fixed-event/every-training-day | 1.00 | hill_climbing | 3→0 | +0.0 | 3 | 20.9 |
| fb-base-001/fixed-event/every-training-day | 1.00 | simulated_annealing | 3→0 | +0.0 | 3 | 5.3 |
| fb-base-001/missed/session-0 | 0.33 | hill_climbing | 0→0 | +0.0 | 1 | 3.1 |
| fb-base-001/missed/session-0 | 0.33 | simulated_annealing | 0→0 | +0.0 | 0 | 4.8 |
| fb-base-001/missed/session-1 | 0.33 | hill_climbing | 0→0 | +0.0 | 1 | 3.3 |
| fb-base-001/missed/session-1 | 0.33 | simulated_annealing | 0→0 | +0.0 | 0 | 4.9 |
| fb-base-001/missed/session-2 | 0.33 | hill_climbing | 0→0 | +0.0 | 1 | 3.2 |
| fb-base-001/missed/session-2 | 0.33 | simulated_annealing | 0→0 | +0.0 | 0 | 5.0 |
| fb-base-001/state/recovered | 0.00 | hill_climbing | 0→0 | +0.0 | 0 | 0.0 |
| fb-base-001/state/recovered | 0.00 | simulated_annealing | 0→0 | +0.0 | 0 | 0.1 |
| fb-base-001/state/high-fatigue | 0.33 | hill_climbing | 0→0 | +0.0 | 1 | 3.3 |
| fb-base-001/state/high-fatigue | 0.33 | simulated_annealing | 0→0 | +0.0 | 0 | 4.9 |
| fb-base-001/state/low-sleep | 0.33 | hill_climbing | 0→0 | +0.0 | 1 | 3.3 |
| fb-base-001/state/low-sleep | 0.33 | simulated_annealing | 0→0 | +0.0 | 0 | 5.1 |
| fb-base-001/manual/to-free-slot | 0.33 | hill_climbing | 0→0 | +0.0 | 1 | 3.1 |
| fb-base-001/manual/to-free-slot | 0.33 | simulated_annealing | 0→0 | +0.0 | 0 | 4.9 |
| fb-base-001/manual/onto-other-session | 0.33 | hill_climbing | 0→0 | +0.0 | 1 | 3.3 |
| fb-base-001/manual/onto-other-session | 0.33 | simulated_annealing | 0→0 | +0.0 | 0 | 4.7 |

## Threshold calibration (HC vs SA)

| bucket | algorithm | mean score delta | mean hard cleared | mean moved | mean ms |
|---|---|---|---|---|---|
| intensity <= 0.3 | hill_climbing | +0.00 | 0.30 | 1.00 | 4.7 |
| intensity <= 0.3 | simulated_annealing | +0.00 | 0.30 | 0.30 | 7.4 |
| intensity > 0.3 | hill_climbing | +0.00 | 1.23 | 1.77 | 16.2 |
| intensity > 0.3 | simulated_annealing | +0.00 | 1.23 | 1.23 | 5.5 |

- **intensity <= 0.3**: hill_climbing clears 0.00 more hard violations on average.
- **intensity > 0.3**: hill_climbing clears 0.00 more hard violations on average.

Routing keeps `HC_AFFECTED_RATIO_THRESHOLD = 0.3`: below it steepest-ascent HC matches SA at lower cost; above it SA clears the same hard violations with fewer moved sessions and lower runtime, because random sampling beats exhaustive neighbourhood sweeps once most of the plan is movable.
