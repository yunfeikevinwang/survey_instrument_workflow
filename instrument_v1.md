## `Consumer AI Survey — Instrument v1`

```
Images: Google Drive folder /images_v1, <Drive folder link>
Embedded data from the URL: PROLIFIC_PID
Force response on all questions unless noted
Page timers: every page
```

## `Consent`

##### `Intro: Text [QID1]`

`consent_header_logo.png`

**Welcome to the study** `Heading`

This survey takes about *10 minutes*.
Your answers are anonymous.

##### `Consent: Multiple choice, single answer [QID2]`

**Do you agree to participate?**

- I agree
- I do not agree `→ End of survey`

## `AI usage`

##### `UsedAI: Multiple choice, single answer [QID3]`

**Have you used an AI chatbot in the past 30 days?**

- Yes
- No `→ Skip to Demographics`

##### `ChatbotsUsed: Multiple choice, select all that apply. Randomize options except "Other" and "None of these". [QID4]`

**Which of these chatbots have you used?** _(Select all that apply)_

- ChatGPT
- Claude
- Gemini
- Other: `text entry box`
- None of these `exclusive`

`Set [chatbots_used] = options selected`

---

##### `WeeklyHours: Text entry, numeric 0–168 [QID5]`

**Roughly how many hours per week do you use `[chatbots_used]`?**

`Set [weekly_hours] = answer`

## `Treatment`

`Before this block: randomly assign [treatment_arm] = "info" or "control" (50/50)`

##### `InfoArm: Text. Display if [treatment_arm] == "info". [QID6]`

Many people use **more than one** chatbot.
Below is a short comparison.

`q5a_comparison_chart.png`

##### `ControlArm: Text. Display if [treatment_arm] == "control". [QID7]`

Please continue to the next page.

## `Demographics`

##### `Age: Multiple choice, single answer [QID8]`

**What is your age?**

- 18–24
- 25–34
- 35–44
- 45 or older
