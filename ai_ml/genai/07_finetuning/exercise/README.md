# Exercise: DPO Dataset — Teaching Preferences

## Background

You've done SFT (Supervised Fine-Tuning), which teaches the model "what to say."
Now you want to teach it "what NOT to say" — more specifically, to prefer helpful, concise responses over verbose, unhelpful ones.

This is what DPO (Direct Preference Optimization) does. It trains on preference pairs:
- **chosen**: the response you want the model to prefer
- **rejected**: the response you want the model to avoid

## Your Task

Create a DPO dataset in `solution/dpo_dataset.jsonl` with at least 10 examples for a customer support chatbot.

Each example must have:
```json
{
  "prompt": "Customer message here",
  "chosen": "The good response (helpful, concise, empathetic)",
  "rejected": "The bad response (verbose, unhelpful, or passive-aggressive)"
}
```

## Example Entry

```json
{
  "prompt": "My order hasn't arrived yet. It's been 2 weeks.",
  "chosen": "I'm sorry for the delay! Your order #XYZ is currently in transit and should arrive within 2 business days. I'll send you a tracking link right now.",
  "rejected": "We apologize for any inconvenience this may have caused. As per our shipping policy, delivery times can vary depending on your location and various external factors that may be beyond our control. We recommend checking your tracking number, which was sent in your confirmation email at the time of your purchase."
}
```

Notice:
- **chosen**: Gets to the point, takes action, shows empathy.
- **rejected**: Verbose, deflects responsibility, tells the user to solve it themselves.

Write 10 realistic pairs covering: refund requests, technical issues, shipping delays, wrong items, and account problems.

This dataset format is exactly what you'd use with the `trl` library's `DPOTrainer`.
