# Consumer AI Survey — Instrument v1

Images: [Google Drive folder](https://drive.google.com/drive/folders/REPLACE_WITH_FOLDER_ID)

```
Survey setup:
- Embedded data: PROLIFIC_PID (from URL), treatment_arm (set by randomizer)
- Force response on all questions unless noted
```

## Block 1: Consent

[[consent_header_logo.png]]

**Welcome!**
This survey takes about *10 minutes*.
Your answers are anonymous.

**Q1. Do you agree to participate?**

- I agree
- I do not agree `→ End of survey`

## Block 2: AI usage

`Show if Q1 = "I agree"`

**Q2. Have you used an AI chatbot in the past 30 days?**

- Yes
- No `→ Skip to Block 4`

**Q3. Which of these chatbots have you used?** *(Select all that apply)*

`Multiple choice, multi-select. Randomize options 1–3.`

1. ChatGPT
2. Claude
3. Gemini
4. Other: ______ `text entry`
5. None of these `exclusive; anchor bottom`

**Q4. Roughly how many hours per week do you use ${q://QID3/ChoiceGroup/SelectedChoices}?**

`Numeric validation: 0–168. Store as weekly_hours.`

## Block 3: Treatment

```
If treatment_arm = "info":
  Show Q5a
Else:
  Show Q5b
```

### Q5a (information arm)

Many people use **more than one** chatbot.
Below is a short comparison.

[[q5a_comparison_chart.png]]

### Q5b (control arm)

Please continue to the next page.

## Block 4: Demographics

**Q6. What is your age?**

- 18–24
- 25–34
- 35–44
- 45 or older
