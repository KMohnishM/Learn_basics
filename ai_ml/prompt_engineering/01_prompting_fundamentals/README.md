# Module 1: Prompting Fundamentals

## 1. Introduction to Prompt Engineering

Welcome to the foundational module on Prompt Engineering. In this module, we will explore the core concepts that govern how large language models (LLMs) interpret, process, and respond to input prompts. Prompt engineering is not merely about asking questions; it is a rigorous discipline that requires a deep understanding of natural language processing (NLP) architectures, specifically Transformer models, and how they leverage self-attention mechanisms to generate coherent and contextually relevant text.

The techniques discussed in this module will form the bedrock of your interactions with language models, enabling you to build robust, reliable, and scalable AI applications. We will dive deep into In-Context Learning, Prompt Anatomy, Structured Outputs, and Context Window Dynamics. The field of Prompt Engineering has rapidly evolved from simple heuristic-based prompt tweaking into a structured engineering discipline, requiring systematic evaluation, version control, and deep architectural understanding of the underlying models.

---

## 2. In-Context Learning (ICL) Mechanics

In-Context Learning (ICL) is a paradigm where an LLM learns to perform a task simply by conditioning on a sequence of demonstrations provided in the input prompt, without any parameter updates (i.e., no backpropagation or fine-tuning). This capability emerges from the massive pre-training phase, where the model learns to infer latent concepts and relationships from sequences of tokens.

### 2.1 The Theory of In-Context Learning

When an LLM processes a prompt containing demonstrations, the self-attention mechanism within the Transformer architecture allows the model to compute representations that encapsulate the relationships between the inputs and outputs provided in the examples. The attention heads learn to "attend" to the demonstrations, essentially constructing an implicit task representation on the fly. 

Unlike traditional supervised learning where weights are adjusted via gradient descent to minimize a loss function, ICL operates entirely within the forward pass of the model. The prompt acts as a temporary context that biases the model's generation probability distribution towards the desired output format and semantic space. The theoretical understanding of ICL suggests that the LLM performs a form of implicit Bayesian inference or gradient descent purely through attention mechanisms over the context window.

### 2.2 Zero-Shot, Few-Shot, and Many-Shot Prompting

The effectiveness of ICL is highly dependent on the number and quality of demonstrations provided in the prompt. We categorize ICL into three main approaches based on the number of examples:

#### 2.2.1 Zero-Shot Prompting

Zero-shot prompting involves presenting a task to the model without any demonstrations. The model relies entirely on its pre-trained knowledge to understand the task instruction and generate a response. This is highly effective for tasks closely aligned with the pre-training distribution (like translation or basic summarization).

**Example: Zero-Shot Sentiment Analysis and Extraction**

```python
import os
import json
import openai
from typing import Dict, Any

# Ensure you have your OPENAI_API_KEY set in your environment
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def zero_shot_extraction_and_sentiment(text: str) -> Dict[str, Any]:
    """
    Perform zero-shot extraction of key entities and determine the overall sentiment.
    This demonstrates asking the model to perform multiple sub-tasks zero-shot.
    
    Args:
        text (str): The raw text to process.
        
    Returns:
        Dict[str, Any]: Parsed JSON dictionary containing extracted data.
    """
    system_instruction = (
        "You are an expert financial analyst AI. Your task is to extract "
        "key entities (Companies, People, Financial Figures) and determine "
        "the overall sentiment (Bullish, Bearish, Neutral) of the provided text. "
        "Output the result as a valid JSON string without markdown formatting."
    )
    
    prompt = f"Analyze the following financial news excerpt:\n\n{text}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=500
        )
        # Parse the JSON string returned by the model
        result_json_str = response.choices[0].message.content.strip()
        return json.loads(result_json_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return {}
    except Exception as e:
        print(f"API Error: {e}")
        return {}

sample_text = (
    "Acme Corp announced record Q3 earnings today, reporting a 25% increase "
    "in year-over-year revenue to $1.2 billion. CEO Jane Doe stated that "
    "the new product line exceeded all expectations. However, competitor "
    "Globex Inc saw their shares tumble after missing targets by $50 million."
)

if __name__ == "__main__":
    result = zero_shot_extraction_and_sentiment(sample_text)
    print(json.dumps(result, indent=2))
```

#### 2.2.2 Few-Shot Prompting

Few-shot prompting introduces a small number of demonstrations (typically 1 to 10) into the prompt. This provides the model with concrete examples of the expected input-output mapping, significantly improving performance, especially on complex, nuanced tasks, or tasks requiring strict output formatting that is difficult to describe purely via instructions.

**Example: Few-Shot Complex Classification with Rationale**

```python
import os
import openai

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def few_shot_medical_triage(symptoms: str) -> str:
    """
    Perform few-shot classification for medical triage, requiring a rationale.
    Providing examples of the *reasoning* process (Chain-of-Thought) alongside 
    the final classification significantly boosts accuracy.
    """
    prompt = f"""
    You are an AI triage assistant. Based on the patient's symptoms, classify the urgency 
    as 'Critical', 'Urgent', or 'Routine'. You must also provide a brief rationale.
    
    Example 1:
    Patient Symptoms: "I have a crushing pain in the center of my chest that radiates to my left arm. I am sweating profusely and feel short of breath."
    Rationale: Chest pain radiating to the arm with diaphoresis and shortness of breath are classic signs of myocardial infarction (heart attack), requiring immediate life-saving intervention.
    Classification: Critical
    
    Example 2:
    Patient Symptoms: "I have had a runny nose, mild sore throat, and a low-grade fever of 99.5F for the past two days."
    Rationale: These symptoms are consistent with a mild viral upper respiratory tract infection (common cold). There are no red flag symptoms requiring immediate care.
    Classification: Routine
    
    Example 3:
    Patient Symptoms: "I fell off my bike and have a deep laceration on my forearm. It is bleeding steadily, but I can still move my fingers."
    Rationale: A deep, actively bleeding laceration requires prompt medical evaluation and likely sutures to prevent infection and ensure proper healing, but it is not immediately life-threatening.
    Classification: Urgent
    
    Patient Symptoms: "{symptoms}"
    Rationale:
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    print(few_shot_medical_triage("I have severe, sudden-onset pain in my lower right abdomen, accompanied by nausea and vomiting."))
```

#### 2.2.3 Many-Shot Prompting

With the advent of models supporting massive context windows (e.g., 128k to 2M tokens), many-shot prompting has become viable. This involves providing 50, 100, or even 1000+ demonstrations. Many-shot prompting can bridge the gap between few-shot ICL and fine-tuning, often achieving comparable performance without the operational overhead of managing fine-tuned models.

When employing many-shot prompting, the model can infer highly complex, nuanced patterns that are impossible to convey in a few examples. However, this approach requires careful management of the context window, prompt caching to reduce latency, and token cost optimization.

### 2.3 Demonstration Selection Strategies

The examples you choose for few-shot or many-shot prompting drastically impact performance. Randomly selecting examples from a training set is often suboptimal and can introduce noise or conflicting signals.

#### 2.3.1 k-Nearest Neighbors (k-NN) Retrieval

A highly effective strategy is to retrieve demonstrations that are semantically similar to the current input query. This is achieved by embedding both the query and a large pool of candidate demonstrations into a vector space, and then selecting the k-nearest neighbors (k-NN) to the query. This is a foundational concept behind Retrieval-Augmented Generation (RAG) applied directly to prompt construction.

**Comprehensive Implementation of k-NN Retrieval for Few-Shot Examples using OpenAI and NumPy**

```python
import numpy as np
from typing import List, Dict, Tuple
import openai
from sklearn.metrics.pairwise import cosine_similarity
import json

class AdvancedKNNFewShotSelector:
    """
    A robust class for dynamically selecting the most relevant few-shot examples
    based on semantic similarity using OpenAI embeddings.
    """
    def __init__(self, candidate_examples: List[Dict[str, str]], embedding_model: str = "text-embedding-3-small"):
        """
        Initialize the selector, computing and caching embeddings for all candidates.
        """
        self.candidate_examples = candidate_examples
        self.embedding_model = embedding_model
        self.client = openai.OpenAI()
        
        # Pre-compute embeddings during initialization to save time during inference
        print(f"Computing embeddings for {len(candidate_examples)} candidate examples...")
        texts_to_embed = [ex['input'] for ex in candidate_examples]
        self.embeddings = self._get_embeddings_batch(texts_to_embed)
        print("Embeddings computed successfully.")
        
    def _get_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """
        Fetch embeddings for a batch of texts in a single API call.
        """
        # Handle empty lists gracefully
        if not texts:
            return np.array([])
            
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.embedding_model
            )
            # Ensure the embeddings are returned in the correct order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            embeddings = [data.embedding for data in sorted_data]
            return np.array(embeddings)
        except Exception as e:
            print(f"Error fetching embeddings: {e}")
            raise
        
    def select_examples(self, query: str, k: int = 3) -> List[Dict[str, str]]:
        """
        Retrieve the k candidate examples that are semantically most similar to the query.
        """
        if k <= 0 or not self.candidate_examples:
            return []
            
        if k >= len(self.candidate_examples):
            return self.candidate_examples.copy()
            
        # 1. Embed the incoming query
        query_embedding_matrix = self._get_embeddings_batch([query])
        if query_embedding_matrix.size == 0:
            return []
        query_embedding = query_embedding_matrix[0]
        
        # 2. Compute cosine similarity against all cached candidate embeddings
        # Reshape to 2D arrays for scikit-learn
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        
        # 3. Find the indices of the top k highest similarity scores
        # argsort returns indices sorting from lowest to highest, so we take the last k and reverse
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        # 4. Map indices back to the original examples
        selected_examples = [self.candidate_examples[i] for i in top_k_indices]
            
        return selected_examples

# Detailed Example Usage Context
if __name__ == "__main__":
    # A larger pool of candidates spanning different domains
    training_data_pool = [
        {"input": "The battery life on this laptop is abysmal. It dies within two hours.", "output": "Hardware - Negative"},
        {"input": "The 4K display is stunning, colors are incredibly vibrant.", "output": "Hardware - Positive"},
        {"input": "The trackpad is unresponsive and erratic.", "output": "Hardware - Negative"},
        {"input": "Customer support was very polite and resolved my issue in 10 minutes.", "output": "Support - Positive"},
        {"input": "I waited on hold for an hour and the agent was rude.", "output": "Support - Negative"},
        {"input": "The software update crashed my entire system, losing hours of work.", "output": "Software - Negative"},
        {"input": "The new UI is clean, intuitive, and much faster than the old version.", "output": "Software - Positive"}
    ]

    try:
        selector = AdvancedKNNFewShotSelector(training_data_pool)
        
        test_queries = [
            "My screen has a massive scratch on it out of the box.",
            "The new dark mode feature looks amazing."
        ]
        
        for q in test_queries:
            print(f"\n--- Query: '{q}' ---")
            dynamic_examples = selector.select_examples(q, k=2)
            for i, ex in enumerate(dynamic_examples):
                print(f"Example {i+1}: Input: '{ex['input']}' => Output: '{ex['output']}'")
                
    except Exception as e:
        print(f"Failed to run k-NN selector: {e}")
```

#### 2.3.2 Class Balancing and Distribution

When selecting examples for classification tasks, it is crucial to maintain a balanced distribution of classes in the prompt. If the demonstrations are heavily skewed towards a specific class, the model may develop a bias, predicting that class disproportionately regardless of the input.

Ensure that the selected examples represent the target distribution. In true few-shot settings, providing an equal number of examples per class is generally the best practice. For instance, if classifying sentiment into Positive, Negative, and Neutral, providing exactly two examples of each is vastly superior to providing five Positive and one Negative.

#### 2.3.3 Recency Bias and Example Ordering

Language models are subject to recency bias (also known as the "majority label bias" or "last example bias"). The model tends to be disproportionately influenced by the examples placed closest to the end of the prompt (i.e., immediately preceding the actual task query).

If the last demonstration always belongs to Class A, the model might incorrectly predict Class A for ambiguous inputs simply due to its position in the context. To mitigate this, practitioners often randomize the order of examples or employ careful interleaving of classes across multiple requests.

---

## 3. Prompt Anatomy & Message Formatting

A well-structured prompt is analogous to a well-structured API request. It must clearly delineate instructions, context, input data, and expected output formats. Modern LLM APIs (like OpenAI's Chat Completions, Anthropic's Messages API) provide specific structures to enforce this separation, moving away from single massive text strings.

### 3.1 System vs. User vs. Assistant Roles

The ChatML (Chat Markup Language) format and similar message-based APIs separate inputs into distinct roles, allowing the model to differentiate between foundational instructions, user queries, and its own past generations.

#### 3.1.1 The System Message

The System message is the highest-level directive. It defines the persona, overarching rules, behavioral constraints, and output format. The model is typically trained to assign exceptionally high weight to the system instructions, making it the ideal place for critical safety guidelines and structural rules.

**Detailed System Prompt Architecture**
A robust system prompt should be heavily structured. Do not write a single paragraph; use lists, headers, and explicit constraints.

```xml
<role>
You are an expert Principal Software Engineer specializing in distributed systems architecture and Go (Golang).
</role>

<core_directives>
1. Always prioritize architectural scalability, fault tolerance, and observability.
2. Provide concrete, runnable code examples using standard Go idioms (e.g., proper error handling, context usage).
3. Explain the "why" behind every architectural decision. Discuss trade-offs explicitly.
4. Do not provide basic syntax explanations. Assume the user is an intermediate to advanced developer.
</core_directives>

<output_constraints>
- All code blocks must specify the language (e.g., ```go).
- Never apologize (e.g., "I'm sorry, I cannot..."). Simply state the limitation and provide the best available alternative.
</output_constraints>
```

#### 3.1.2 The User Message

The User message represents the specific query, task, or input data provided by the human (or calling application) for the current turn of the conversation. It should ideally be concise and reference the instructions laid out in the system prompt.

#### 3.1.3 The Assistant Message

The Assistant message represents the model's response. A powerful advanced technique is "pre-filling" the assistant message. By appending a partial assistant message to the end of the message array, you can force the model to begin its generation with specific syntax, effectively bypassing refusals or guaranteeing output formats.

*Note: Pre-filling is fully supported by Anthropic's Claude API, and partially supported by open-source models, but less strictly adhered to by OpenAI's current chat endpoints.*

### 3.2 Persona & Role Steering

Assigning a persona to the model in the system prompt is a powerful technique to align the tone, complexity, and perspective of the output. By defining a specific role (e.g., "Senior Cybersecurity Analyst," "Empathetic Therapist," "Rigorous Academic Reviewer"), you activate specific regions of the model's latent space associated with that domain's vocabulary and analytical patterns.

Role steering not only changes the vocabulary used but often improves the accuracy of the response, as it forces the model to adhere to the rigorous constraints and knowledge base typical of that persona, suppressing hallucinations common in generic "helpful assistant" personas.

### 3.3 Delimiters and Context Segregation

When dealing with complex prompts containing instructions, reference documents, user inputs, and schemas, it is essential to segregate these components clearly. Failure to do so can lead to instruction tuning cross-contamination, where the model interprets user input data as an instruction to follow (a vulnerability known as prompt injection).

Using clear delimiters helps the model parse the prompt accurately.

#### 3.3.1 Markdown Segregation

Markdown headings (`#`, `##`) and bold text (`**`) are commonly used to create structure. However, they lack robustness for strict programmatic segregation, especially if the input data (e.g., a scraped web page) also contains markdown, leading to confusion about where the instruction ends and the data begins.

#### 3.3.2 XML Tags (Industry Standard)

XML tags are highly effective for delineating sections of a prompt. Models, especially those trained by Anthropic, are heavily optimized to recognize XML tag boundaries perfectly. They allow for hierarchical nesting and clear boundaries.

```python
prompt_with_xml = """
Please summarize the following financial document based on the specific focus areas provided.

<focus_areas>
<area>Financial performance and Q3 revenue growth metrics</area>
<area>New enterprise product announcements</area>
<area>Executive leadership changes and restructuring</area>
</focus_areas>

<document>
<title>Q3 Investor Relations Update</title>
<content>
We are pleased to announce our Q3 results. Revenue grew by 15.2% year-over-year, reaching a record $2.4B, driven largely by the successful launch of our new enterprise cloud platform, CloudScale X. Furthermore, we are thrilled to welcome Jane Doe as our new Chief Technology Officer, replacing John Smith who is retiring. Jane brings decades of experience from her previous role at TechTitan...
</content>
</document>

Based ONLY on the <document> provided, write the summary. Provide the summary enclosed strictly within <summary> tags.
"""
```

#### 3.3.3 JSON Fences

For structured data inputs, enclosing information in JSON code fences (```json ... ```) is optimal. It signals to the model that the enclosed text should be parsed strictly as data structures, not as natural language instructions.

---

## 4. Structured Outputs & Constrained Decoding

A critical challenge in building production LLM applications (agents, data pipelines, integrations) is ensuring that the model's output adheres to a specific, machine-readable format (e.g., JSON, YAML, SQL). Relying solely on prompt engineering ("You must output JSON. Do not output anything else. I mean it.") often results in parsing errors due to extraneous conversational text ("Here is your JSON:"), invalid syntax (trailing commas, unescaped quotes), or missing required fields.

### 4.1 Native JSON Mode

Many LLM providers offer a native "JSON Mode" (e.g., passing `response_format={ "type": "json_object" }` in OpenAI). This enforces at the API level that the output will be syntactically valid JSON. However, it does *not* guarantee schema adherence. It will not guarantee that specific keys are present, nor will it guarantee that the values are of the correct type (e.g., it might output a string "10" instead of an integer 10).

### 4.2 Grammar-Constrained Decoding

To guarantee schema adherence, we must use Grammar-Constrained Decoding. This technique intervenes at the inference level (during the autoregressive generation of each token). The decoder's logit distribution is intercepted. The system is restricted to only select tokens that are valid according to a predefined grammar (like a JSON Schema or a Regex definition). If a token would violate the schema (e.g., predicting an alphabet character when an integer is required by the schema), its probability is masked to zero before sampling.

#### 4.2.1 OpenAI Structured Outputs (Strict Mode)

OpenAI recently introduced robust Structured Outputs, which leverages constrained decoding on their backend to guarantee that the output exactly matches a provided JSON Schema. It is fully integrated with Pydantic V2 in their Python SDK.

**Comprehensive Example: Complex Data Extraction with Pydantic and OpenAI Structured Outputs**

```python
import os
import json
import openai
from pydantic import BaseModel, Field
from typing import List, Optional

# Define a deeply nested Pydantic schema using Pydantic V2
class DeveloperExperience(BaseModel):
    company_name: str = Field(description="Name of the company")
    role: str = Field(description="Job title")
    duration_years: float = Field(description="Duration in years (approximate)")
    key_technologies: List[str] = Field(description="Primary programming languages and tools used")

class CandidateProfile(BaseModel):
    full_name: str = Field(description="First and last name")
    email: Optional[str] = Field(description="Contact email address, if present", default=None)
    github_url: Optional[str] = Field(description="GitHub profile URL", default=None)
    years_of_experience: int = Field(description="Total calculated years of professional experience")
    experience_history: List[DeveloperExperience] = Field(description="Chronological list of past roles")
    is_senior: bool = Field(description="True if years_of_experience >= 5, else False")
    summary: str = Field(description="A concise 2-sentence professional summary")

def parse_resume(resume_text: str) -> CandidateProfile:
    """
    Extract structured candidate data from an unstructured resume text block,
    guaranteed to match the Pydantic schema perfectly.
    """
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    system_prompt = (
        "You are an expert HR data extraction system. Your task is to extract "
        "structured data from resumes. You must adhere perfectly to the schema."
    )
    
    try:
        # We use beta.chat.completions.parse to utilize Structured Outputs
        response = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06", # Structured outputs require newer models
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Resume Text:\n\n{resume_text}"}
            ],
            response_format=CandidateProfile,
        )
        
        # The SDK automatically parses the JSON string into the Pydantic object
        parsed_data: CandidateProfile = response.choices[0].message.parsed
        return parsed_data
        
    except Exception as e:
        print(f"Extraction failed: {e}")
        raise

# Example Usage
sample_resume = """
Johnathan A. Doe
jdoe.engineer@example.com | github.com/jdoe_codes

Experience:
Senior Backend Engineer, DataTech Solutions (2019 - Present)
- Architected microservices using Go and gRPC, reducing latency by 40%.
- Managed PostgreSQL clusters and Redis caches.

Software Developer, WebWizards LLC (2016 - 2019)
- Built monolithic web apps using Python, Django, and React.
- Deployed to AWS EC2.
"""

if __name__ == "__main__":
    try:
        profile = parse_resume(sample_resume)
        print("Successfully Extracted Profile:")
        # Dump to JSON for clean visualization
        print(profile.model_dump_json(indent=2))
        
        # Verify schema enforcement programmatic access
        assert isinstance(profile.is_senior, bool)
        assert len(profile.experience_history) == 2
        print("\nData Types Verified Programmatically.")
        
    except Exception as e:
        print("Failed to run extraction example.")
```

#### 4.2.2 Open-Source Constrained Decoding (Outlines)

For self-hosted open-source models (e.g., Llama 3, Mistral, Qwen) running on local hardware or dedicated endpoints, you cannot rely on OpenAI's backend. Instead, libraries like `outlines`, `guidance`, and `llama.cpp` provide the constrained decoding layer. 

These libraries construct Finite State Machines (FSMs) based on your Pydantic schema or Regular Expression. During the generation loop, the FSM actively dictates the allowed token transitions by manipulating the logits before softmax. This ensures 100% adherence to the constraints without relying on a proprietary API, and often significantly speeds up generation because the model doesn't waste time predicting invalid tokens.

**Conceptual Example: Strict Regex Generation with Outlines**

```python
# Note: This conceptual block demonstrates the API of the outlines library.
# It requires a local model weights file or huggingface access to run.
"""
import outlines
from pydantic import BaseModel, constr

# 1. Load the model (can be huggingface transformers, vLLM, or GGUF)
model = outlines.models.transformers("mistralai/Mistral-7B-Instruct-v0.2")

# 2. Define a strict schema with regex constraints.
class NetworkConfig(BaseModel):
    # Regex for exactly an IPv4 address
    ip_address: constr(pattern=r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
    port: int

# 3. Create the constrained generator
generator = outlines.generate.json(model, NetworkConfig)

# 4. Generate
prompt = "Configure a local server on port 8080 using the standard loopback address."
result = generator(prompt) 
print(f"Generated Config: {result}")
"""
```

Constrained decoding fundamentally changes the reliability of LLMs, moving them from probabilistic text generators to deterministic data extraction engines, a prerequisite for building reliable autonomous agents.

---

## 5. Context Window Dynamics & Token Utilization

The context window is the maximum sequence of tokens (input prompt + generated output) an LLM can process in a single request. Understanding how models behave within this window—which has grown from 2k tokens in early models to over 2 Million tokens in models like Gemini 1.5 Pro—is crucial for tasks involving large document analysis, codebase reasoning, or long conversation histories.

### 5.1 The "Lost in the Middle" Phenomenon

Groundbreaking research (e.g., Liu et al., "Lost in the Middle") has consistently shown that LLMs do not pay equal attention to all parts of a massive context window. They exhibit a U-shaped performance curve:
- **Primacy Bias:** High accuracy retrieving information from the very beginning of the prompt.
- **Recency Bias:** High accuracy retrieving information from the very end of the prompt.
- **The Trough:** Performance drops significantly for information buried in the middle of a long context.

This phenomenon occurs because the self-attention mechanism struggles to isolate relevant signal vectors from a massive amount of surrounding noise. The model's ability to reason over multiple scattered facts within the middle of the context degrades rapidly, even if it can technically "see" them.

### 5.2 Needle in a Haystack (NIAH) Evaluation

The Needle in a Haystack (NIAH) evaluation metric measures an LLM's ability to retrieve a specific, isolated fact (the "needle") hidden within a massive body of irrelevant text (the "haystack") at various insertion depths within the context window.

While modern frontier models achieve near-perfect 100% NIAH scores across million-token windows, it is critical to distinguish between *simple retrieval* (finding a direct quote) and *complex reasoning* (synthesizing information). A model may perfectly find a needle, but if you ask it to synthesize a conclusion from five different needles spread across 500k tokens, performance will still degrade. Do not confuse a large context window with infinite reasoning capacity.

### 5.3 Strategic Context Placement (Prompt Layout Engineering)

To mitigate the "Lost in the Middle" effect and optimize for attention mechanics, prompt engineers must be highly strategic about where information is placed within the context window. 

**Core Rules of Layout Engineering:**
1. **Place critical instructions and output schemas at the very end:** Always append the specific question, the final instruction, and the requested output schema (like a JSON template) as the final text in the prompt. This leverages recency bias to ensure the model focuses on the immediate task and formatting rules at the exact moment it begins generating tokens.
2. **Place reference documents in the middle:** Insert the massive, bulky content—background context, RAG search results, database dumps, or long documents—in the middle of the prompt. Accept that some middle-context degradation may occur, but shield your instructions from it.
3. **Place system directives at the very beginning:** The system prompt, overarching persona definitions, and foundational security constraints should remain at the very beginning (leveraging primacy bias).

**Optimal Prompt Structure Template Architecture:**

```xml
<system_instructions>
<!-- [START] Highest priority persona, rules, and constraints (Primacy Bias) -->
You are a senior legal assistant. You must analyze contracts for indemnification clauses.
</system_instructions>

<background_context>
<!-- [MIDDLE] Bulky text, retrieved context, historical data, transcripts -->
<document id="doc_1">
[... 50,000 tokens of contract text ...]
</document>
</background_context>

<examples>
<!-- [MIDDLE-END] Few-shot demonstrations to prime the output style -->
<example>
Input: [Short excerpt]
Output: {"contains_clause": true, "risk_level": "High"}
</example>
</examples>

<user_query>
<!-- [END] The specific task to execute based on the context (Recency Bias) -->
Analyze doc_1 and extract all indemnification clauses.
</user_query>

<output_format>
<!-- [ABSOLUTE END] Strict instructions on how to format the answer -->
Return the analysis as a JSON array of objects. Do not include markdown formatting.
</output_format>
```

### 5.4 Prompt Templates and Programmatic Management

As AI applications scale from prototypes to production systems, hardcoding prompt strings with inline variables becomes unmaintainable. Prompt templates provide a structured, versionable way to inject dynamic runtime data into predefined architectural prompt structures.

#### 5.4.1 Python f-strings (The Baseline)

For simple, single-turn applications, native Python f-strings or `str.format()` are often sufficient and highly readable. They lack logic (loops, conditionals) but are incredibly fast.

```python
def create_basic_summary_prompt(document: str, max_words: int) -> str:
    """A fast, simple f-string prompt."""
    return f"""
    Please summarize the following document in strictly under {max_words} words.
    
    <document>
    {document}
    </document>
    
    Summary:
    """
```

#### 5.4.2 Jinja2 Templates (Industry Standard for Logic)

For complex prompts requiring conditional logic (if/else), loops (iterating over an arbitrary list of RAG chunks or few-shot examples), and inheritance (sharing a base system prompt across multiple endpoints), Jinja2 is the industry standard. It cleanly separates the prompt structure (presentation logic) from the Python application code (business logic).

**Comprehensive Example: Dynamic Jinja2 Prompt Template for RAG**

```python
from jinja2 import Template

# Define the template string (this would typically live in a .jinja file)
rag_prompt_template = """
<system>
You are an intelligent knowledge base assistant.
{% if strict_mode %}
CRITICAL RULE: You must answer based ONLY on the provided documents. If the documents do not contain the answer, reply exactly with: "I do not have enough information." Do not hallucinate external knowledge.
{% endif %}
</system>

<context>
Here are the retrieved documents relevant to the user query:
{% for doc in retrieved_documents %}
<document source="{{ doc.metadata.source }}" relevance="{{ doc.score }}">
{{ doc.page_content }}
</document>
{% else %}
<document>No relevant documents were found in the database.</document>
{% endfor %}
</context>

<user_query>
{{ user_query }}
</user_query>

<instructions>
Based on the <context> above, please answer the <user_query>.
{% if require_citations %}
You MUST cite your sources using the source attribute, e.g., [Source: url].
{% endif %}
</instructions>
"""

# Compile the template
template = Template(rag_prompt_template, trim_blocks=True, lstrip_blocks=True)

# Define mock data representing a RAG retrieval step
mock_docs = [
    {
        "page_content": "The internal VPN is accessed via vpn.company.com using Okta SSO.",
        "metadata": {"source": "wiki/IT/vpn-setup"},
        "score": 0.92
    },
    {
        "page_content": "VPN access requires a hardware security key (YubiKey).",
        "metadata": {"source": "wiki/IT/security-policies"},
        "score": 0.85
    }
]

# Render the template with dynamic runtime variables
final_prompt = template.render(
    strict_mode=True,
    require_citations=True,
    retrieved_documents=mock_docs,
    user_query="How do I connect to the VPN and what authentication is required?"
)

if __name__ == "__main__":
    print(final_prompt)
```

## 6. Conclusion

Prompt Engineering is profoundly more complex than simply chatting with an AI. It involves a systematic, architectural approach to constructing inputs that predictably and reliably extract the desired latent knowledge and behavioral constraints from complex probabilistic models. By mastering In-Context Learning mechanics, implementing rigorous message formatting and layout engineering, enforcing structured outputs through constrained decoding algorithms, and optimizing token utilization via caching and distillation, you elevate your practice from basic heuristic querying to robust AI systems engineering. 

This fundamental module serves as the critical prerequisite for the advanced topics we will explore in subsequent modules, including autonomous agentic workflows, complex tool use, fine-tuning, and robust evaluation frameworks.
