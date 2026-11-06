# `Consumer AI Survey — Instrument v1`

```
Images: Google Drive folder /images_v1
Survey setup:
- Set [PROLIFIC_PID] from URL
- Randomly assign [treatment_arm] = "info" or "control" (50/50)
- Force response on all questions unless noted
```

## `Block 1: Consent`

`consent_header_logo.png`

### Welcome to the study

This survey takes about *10 minutes*.
Your answers are anonymous.

**Do you agree to participate?**

`Q1: Multiple choice, single answer`

- I agree
- I do not agree `→ End of survey`

---

## `Block 2: AI usage`

**Have you used an AI chatbot in the past 30 days?**

`Q2: Multiple choice, single answer`

- Yes
- No `→ Skip to Block 4`

**Which of these chatbots have you used?** _(Select all that apply)_

`Q3: Multiple choice, select all that apply. Randomize options except "Other" and "None of these".`

- ChatGPT
- Claude
- Gemini
- Other: `text entry box`
- None of these `exclusive`

`Set [chatbots_used] = options selected in Q3`

---

**Roughly how many hours per week do you use `[chatbots_used]`?**

`Q4: Text entry, numeric 0–168. Set [weekly_hours] = answer.`

---

## `Block 3: Treatment`

```
If [treatment_arm] = "info": show Q5a
Else: show Q5b
```

### `Q5a: Information arm`

Many people use **more than one** chatbot.
Below is a short comparison.

`q5a_comparison_chart.png`

### `Q5b: Control arm`

Please continue to the next page.

---

## `Block 4: Demographics`

**What is your age?**

`Q6: Multiple choice, single answer`

- 18–24
- 25–34
- 35–44
- 45 or older
