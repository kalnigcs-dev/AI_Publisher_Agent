"""Full End-to-End A-to-Z Autonomous Publishing Pipeline Test."""

import json
from publisher_mcp.database import db
from publisher_mcp.server import save_article, validate_article, publish_article, verify_publication

ARTICLE_HTML = """
<h2>Understanding the Architectural Demands of Reasoning Models</h2>
<p>The release of DeepSeek-R1 has reshaped open-source AI infrastructure by demonstrating that large-scale reinforcement learning can cultivate state-of-the-art mathematical and algorithmic reasoning without human-annotated chains of thought. However, serving reasoning models in enterprise production environments introduces distinct infrastructure bottlenecks compared to standard conversational LLMs.</p>
<p>Unlike traditional language models that output concise answers within hundreds of tokens, reasoning models produce thousands of internal chain-of-thought tokens (enclosed in <code>&lt;think&gt;...&lt;/think&gt;</code> blocks) prior to generating final responses. This dramatic token expansion stresses both GPU compute throughput and Key-Value (KV) cache memory. To serve DeepSeek-R1 and its distilled variants with sub-second Time-to-First-Token (TTFT) and high token generation rates, platform engineering teams are turning to <strong>vLLM</strong>—the high-throughput, PagedAttention-powered serving engine.</p>

<h2>Full 671B MoE vs. Distilled Models: Hardware Sizing Matrix</h2>
<p>Before launching vLLM, infrastructure architects must align their cluster topology with the model scale. DeepSeek-R1 models fall into two distinct deployment profiles:</p>
<ul>
    <li><strong>Full DeepSeek-R1 (671B MoE):</strong> Utilizes a Mixture-of-Experts architecture where 37 billion parameters are activated per token. Deploying the full model requires multi-GPU, multi-node setups—typically a single 8-way NVIDIA H100/H200 (8x 80GB/141GB) node using native FP8 weights, or multi-node clusters across high-speed InfiniBand/RoCE fabrics.</li>
    <li><strong>DeepSeek-R1-Distill-Llama-70B:</strong> Distilled reasoning capabilities ported onto standard dense architectures. While BF16 weights consume ~140 GB of VRAM, an FP8 quantized checkpoint requires only ~70 GB, making it comfortably deployable across a dual-GPU node (2x NVIDIA A100/H100 80GB).</li>
    <li><strong>DeepSeek-R1-Distill-Qwen-14B / 32B:</strong> Ideal for edge nodes, internal department tools, and single-GPU servers (1x A100 80GB or 1x RTX 4090 with 4-bit/8-bit quantization).</li>
</ul>

<h2>Serving Full DeepSeek-R1 with Tensor and Expert Parallelism</h2>
<p>When serving the flagship 671B Mixture-of-Experts model, naive tensor parallelism creates severe inter-GPU communication overhead. vLLM solves this by combining <strong>Tensor Parallelism (TP)</strong> with <strong>Expert Parallelism (EP)</strong> to distribute expert weights across GPU ranks:</p>

<pre><code class="language-bash">vllm serve deepseek-ai/DeepSeek-R1 \
  --trust-remote-code \
  --tensor-parallel-size 8 \
  --enable-expert-parallel \
  --enable-prefix-caching \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.92 \
  --port 8000
</code></pre>

<p>Key configuration flags for enterprise clusters:</p>
<ul>
    <li><code>--enable-expert-parallel</code>: Crucial for DeepSeek's MoE design. It prevents individual GPU ranks from becoming expert dispatch bottlenecks during complex reasoning branches.</li>
    <li><code>--max-model-len 32768</code>: Reasoning tasks generate extensive token traces. Allocating at least 32k tokens prevents context clipping while balancing KV cache availability.</li>
    <li><code>--gpu-memory-utilization 0.92</code>: Dedicates 92% of GPU VRAM to weight storage and dynamic PagedAttention memory pools.</li>
</ul>

<h2>Memory Optimization: Dual-GPU Deployment for Distill-70B</h2>
<p>For organizations operating mid-range AI clusters, <strong>DeepSeek-R1-Distill-Llama-70B</strong> offers premier reasoning performance at a fraction of compute cost. By leveraging dynamic FP8 quantization (such as Neural Magic's pre-quantized weights), the model fits comfortably across two 80GB GPUs:</p>

<pre><code class="language-bash">vllm serve neuralmagic/DeepSeek-R1-Distill-Llama-70B-FP8-dynamic \
  --tensor-parallel-size 2 \
  --dtype bfloat16 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90 \
  --enable-prefix-caching \
  --kv-cache-dtype fp8 \
  --port 8000
</code></pre>

<p>Notice the inclusion of <code>--kv-cache-dtype fp8</code>: this compresses the Key-Value cache from 16-bit to 8-bit precision, effectively doubling the concurrent user request capacity on dual-GPU nodes without measurably degrading reasoning accuracy.</p>

<h2>Accelerating Reasoning Loops with Automatic Prefix Caching (APC)</h2>
<p>One of the most powerful features in vLLM is <strong>Automatic Prefix Caching (APC)</strong>, enabled via <code>--enable-prefix-caching</code>. In reasoning and agentic workflows, requests frequently share large common prefixes: system prompts, enterprise retrieval-augmented generation (RAG) context blocks, and few-shot reasoning scaffolds.</p>
<p>With APC enabled, vLLM tracks radix trees of previously processed prompt tokens. When a new incoming request matches an existing prefix, vLLM skips compute for those prompt tokens and retrieves the cached KV tensors directly. This reduces Time-to-First-Token (TTFT) by up to <strong>85%</strong> on iterative conversational and code generation tasks.</p>

<h2>Production Client Integration: OpenAI-Compatible SDK</h2>
<p>Because vLLM natively implements the standard OpenAI REST API specification, integrating reasoning endpoints into downstream applications requires zero custom SDK dependencies:</p>

<pre><code class="language-python">from openai import OpenAI

client = OpenAI(
    api_key="internal-cluster-key",
    base_url="http://vllm-service.ai-system.svc.cluster.local:8000/v1"
)

response = client.chat.completions.create(
    model="neuralmagic/DeepSeek-R1-Distill-Llama-70B-FP8-dynamic",
    messages=[
        {"role": "system", "content": "You are a senior systems engineer. Provide complete mathematical derivations."},
        {"role": "user", "content": "Analyze the cache hit probability of a radix-tree prefix cache under Zipfian query distributions."}
    ],
    temperature=0.6,
    max_tokens=4096
)

print(response.choices[0].message.content)
</code></pre>

<h2>Verified References & Technical Documentation</h2>
<ul>
    <li><a href="https://docs.vllm.ai/en/latest/models/deepseek_r1.html">Official vLLM Documentation: DeepSeek-R1 Architecture &amp; Serving</a> — vLLM Project Documentation</li>
    <li><a href="https://github.com/vllm-project/vllm">vLLM: High-Throughput and Memory-Efficient LLM Serving Engine</a> — GitHub Repository</li>
    <li><a href="https://huggingface.co/neuralmagic/DeepSeek-R1-Distill-Llama-70B-FP8-dynamic">Neural Magic DeepSeek-R1-Distill-Llama-70B FP8 Model Card</a> — Hugging Face</li>
    <li><a href="https://deepseek.com/r1-techreport">DeepSeek-R1 Technical Report: Reasoning via Large-Scale Reinforcement Learning</a> — DeepSeek AI Research</li>
</ul>
"""

def execute_atoz_test():
    print("==================================================")
    print("STEP 1: SENSING & TOPIC VERIFICATION")
    print("==================================================")
    topic = db.get_topic(2)
    print(f"Topic ID 2: '{topic['title']}' [{topic['status']}] (Section: {topic['section']})")
    sources = db.get_research_sources(2)
    print(f"Verified research sources attached: {len(sources)}")
    for s in sources:
        print(f"  - {s['title']} ({s['url']})")

    print("\n==================================================")
    print("STEP 2: SAVING ARTICLE DRAFT")
    print("==================================================")
    save_res = save_article(
        topic_id=2,
        site_id=1,
        title="Deploying DeepSeek-R1 and Local Reasoning LLMs with vLLM: A Production Architecture Guide",
        slug="deploying-deepseek-r1-with-vllm",
        section="Artificial Intelligence",
        content_html=ARTICLE_HTML.strip(),
        meta_description="A production guide to deploying DeepSeek-R1 and distilled reasoning models with vLLM covering tensor parallelism, FP8 quantization, and prefix caching.",
        change_summary="Initial comprehensive production guide with code and manifests",
    )
    article_id = save_res["article_id"]
    print(f"Article saved in SQLite with ID: {article_id}")

    print("\n==================================================")
    print("STEP 3: RUNNING DETERMINISTIC VALIDATION GATE")
    print("==================================================")
    val_res = validate_article(article_id)
    print("Validation Report:")
    print(f"  - Passed: {val_res['passed']}")
    print(f"  - New Status: {val_res['new_status']}")
    print(f"  - Checks Run: {val_res['checks_run']}")
    print(f"  - Word Count: {val_res['metrics']['word_count']} words")
    print(f"  - Errors: {val_res['errors']}")
    print(f"  - Warnings: {val_res['warnings']}")
    assert val_res["passed"] is True
    assert val_res["new_status"] == "APPROVED"

    print("\n==================================================")
    print("STEP 4: PUBLISHING GATE & LIVE WORDPRESS UPLOAD")
    print("==================================================")
    pub_res = publish_article(article_id=article_id, as_draft=True)
    print("Publication Output:")
    print(json.dumps(pub_res, indent=2))
    assert pub_res["status"] == "success"
    assert pub_res["dry_run"] is False

    print("\n==================================================")
    print("STEP 5: VERIFYING PUBLICATION INTEGRITY")
    print("==================================================")
    ver_res = verify_publication(article_id)
    print("Verification Output:")
    print(json.dumps(ver_res, indent=2))
    assert ver_res["status"] == "verified"

    print("\n==================================================")
    print("STEP 6: FINAL PIPELINE SUMMARY")
    print("==================================================")
    summary = db.get_pipeline_summary()
    print(json.dumps(summary, indent=2))
    print(f"\nALL CHECKS PASSED! Live WordPress Post Link: {pub_res.get('remote_url')}")


if __name__ == "__main__":
    execute_atoz_test()
