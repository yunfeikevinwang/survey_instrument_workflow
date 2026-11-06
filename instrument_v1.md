# `Consumer AI Survey — Instrument v1`

```
Images: Google Drive folder /images_v1
Survey setup:
- Set [PROLIFIC_PID] from URL
- Randomly assign [treatment_arm] = "info" or "control" (50/50)
- Force response on all questions unless noted
```

## `Consent`

##### `QID1: Text`

`consent_header_logo.png`

### Welcome to the study

This survey takes about *10 minutes*.
Your answers are anonymous.

##### `QID2: Multiple choice, single answer`

**Do you agree to participate?**

- I agree
- I do not agree `→ End of survey`

## `AI usage`

##### `QID3: Multiple choice, single answer`

**Have you used an AI chatbot in the past 30 days?**

- Yes
- No `→ Skip to Demographics`

##### `QID4: Multiple choice, select all that apply. Randomize options except "Other" and "None of these".`

**Which of these chatbots have you used?** _(Select all that apply)_

- ChatGPT
- Claude
- Gemini
- Other: `text entry box`
- None of these `exclusive`

`Set [chatbots_used] = options selected`

---

##### `QID5: Text entry, numeric 0–168`

**Roughly how many hours per week do you use `[chatbots_used]`?**

`Set [weekly_hours] = answer`

## `Treatment`

```
If [treatment_arm] = "info": show QID6
Else: show QID7
```

### `Information arm`

##### `QID6: Text`

Many people use **more than one** chatbot.
Below is a short comparison.

`q5a_comparison_chart.png`

### `Control arm`

##### `QID7: Text`

Please continue to the next page.

## `Demographics`

##### `QID8: Multiple choice, single answer`

**What is your age?**

- 18–24
- 25–34
- 35–44
- 45 or older
