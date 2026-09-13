# Exercise: Build a Full Safety Wrapper

## Background

You're shipping a healthcare chatbot that helps patients understand their medical documents.

This is a high-stakes use case. Errors could be dangerous:
- Hallucinations could cause patients to misunderstand their diagnosis.
- The chatbot must **never** give medical advice — only document summarization.
- PII (patient names, DOB, SSN) must never be echoed back in responses.
- The chatbot must never output prescriptions, diagnoses, or treatment recommendations.

## Your Task

Build a `SafeLLMWrapper` class in `solution/safe_llm_wrapper.py` that wraps any LLM call with the following layers:

### Input Layer (before calling LLM)
1. **Topic guard**: If the user asks for medical advice (detect: "should I take", "is it safe to", "can I combine", "what dose"), reject with a polite refusal.
2. **Injection guard**: If the message contains injection keywords, reject it.
3. **Length check**: Reject inputs over 2000 characters.

### Output Layer (after getting LLM response)
4. **PII scan**: Use the regex patterns from the lab to detect if the model accidentally included email, SSN, or credit card numbers in the output.
5. **Advice detection**: If the output contains phrases like "you should", "I recommend", "take this", block it with a fallback message.
6. **Faithfulness check**: If you also have context documents, verify the response only references information in those documents (simplified: check that all nouns in the response appear somewhere in the context).

### Logging
7. Every call should log: `{timestamp, user_id, input_safe, output_safe, blocked_reason}`.

The wrapper should return either:
- The validated LLM response, or
- A safe fallback message explaining why the request was blocked.
