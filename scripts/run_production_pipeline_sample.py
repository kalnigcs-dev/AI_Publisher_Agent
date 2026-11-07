"""Run production-grade article synthesis, deterministic validation, and gated draft publication."""

import json
from publisher_mcp.database import db
from publisher_mcp.server import save_article, validate_article, publish_article, verify_publication

ARTICLE_HTML = """
<h2>Why Platform Teams Are Moving Beyond Ingress-NGINX</h2>
<p>For nearly a decade, the Kubernetes <code>ingress-nginx</code> controller served as the de facto edge routing mechanism for cloud-native workloads. However, the legacy Ingress specification suffers from a fundamental architectural limitation: it is monolithic. In a standard Ingress manifest, edge infrastructure configuration (load balancer provisioning, TLS termination) is coupled directly with application routing rules in a single namespaced resource.</p>
<p>To overcome these constraints, teams turned to proprietary annotations (such as <code>nginx.ingress.kubernetes.io/*</code>) and arbitrary configuration snippets. Over time, this introduced severe annotation sprawl, fragmented routing logic, and brittle configurations that resisted standard validation. With community maintainers signaling long-term retirement and deprecation milestones for legacy controllers, migrating to the official <strong>Kubernetes Gateway API</strong> has transitioned from an optional modernization exercise to an urgent infrastructure requirement.</p>

<h2>The Gateway API Architectural Model: Separation of Concerns</h2>
<p>Maintained by Kubernetes SIG Network, the Gateway API replaces monolithic Ingress with an expressive, role-oriented hierarchy. By establishing clean boundaries across organizational personas, Gateway API enhances security and RBAC governance:</p>
<ul>
    <li><strong>GatewayClass (Infrastructure Provider):</strong> A cluster-scoped resource defining the underlying gateway controller implementation (such as Envoy Gateway, NGINX Gateway Fabric, or cloud managed controllers).</li>
    <li><strong>Gateway (Platform / Cluster Operator):</strong> Defines the network entry points, listening ports (80, 443), TLS termination modes, and namespace attachment constraints (<code>allowedRoutes</code>).</li>
    <li><strong>HTTPRoute (Application Developer):</strong> Namespaced routing declarations that specify path matching, header routing, URL rewriting, and backend Service targets, binding to parent Gateways via <code>parentRefs</code>.</li>
    <li><strong>ReferenceGrant (Cross-Namespace Security):</strong> Enables explicit, audited cross-namespace references (for example, allowing an edge Gateway in <code>gateway-system</code> to bind to an application Service or TLS Secret in a separate tenant namespace).</li>
</ul>

<h2>Automated Manifest Translation with ingress2gateway</h2>
<p>Rather than hand-authoring hundreds of route manifests, platform engineers can leverage <code>ingress2gateway</code>, an open-source CLI developed under Kubernetes SIG Network. Built on a provider/emitter architecture, it translates Ingress declarations into standard Gateway API equivalents while highlighting unconvertible annotations for manual review.</p>

<h3>Installation and CLI Usage</h3>
<pre><code class="language-bash"># Install via Go or package manager
go install github.com/kubernetes-sigs/ingress2gateway@latest

# Translate a single manifest
ingress2gateway print --providers=ingress-nginx --input-file=ingress.yaml > gateway-manifests.yaml

# Translate all Ingress resources in a live production namespace
ingress2gateway print --providers=ingress-nginx --namespace=production > production-routes.yaml

# Full cluster audit and extraction
ingress2gateway print --providers=ingress-nginx --all-namespaces > cluster-gateway-routes.yaml
</code></pre>

<p>The utility automatically maps common annotations to native typed Gateway API filters:</p>
<ul>
    <li><code>nginx.ingress.kubernetes.io/rewrite-target</code> maps natively to the <code>URLRewrite</code> filter.</li>
    <li><code>nginx.ingress.kubernetes.io/ssl-redirect</code> maps natively to the <code>RequestRedirect</code> filter on port 80.</li>
    <li>Header injections map directly to <code>RequestHeaderModifier</code> filters.</li>
</ul>

<h2>Topology Planning: Shared Gateway vs. Dedicated Gateways</h2>
<p>When architecting your Gateway API deployment, selecting the right topology is critical to cloud cost management. As highlighted in production migrations by the Cloud Native Computing Foundation (CNCF), deploying an individual <code>Gateway</code> resource per microservice triggers the provisioning of independent cloud LoadBalancers (e.g., AWS NLB or GCP Forwarding Rules), rapidly escalating cloud infrastructure bills.</p>
<p>For most enterprise workloads, a <strong>Single Shared Gateway</strong> pattern is recommended. A centralized Gateway resource in a dedicated namespace (e.g., <code>gateway-system</code>) manages the external IP and wild-card TLS termination, while individual tenant teams manage isolated <code>HTTPRoute</code> manifests in their respective namespaces.</p>

<h3>Example: Production Shared Gateway Manifest</h3>
<pre><code class="language-yaml">apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: shared-edge-gateway
  namespace: gateway-system
spec:
  gatewayClassName: nginx
  listeners:
  - name: http
    port: 80
    protocol: HTTP
    allowedRoutes:
      namespaces:
        from: All
  - name: https
    port: 443
    protocol: HTTPS
    tls:
      mode: Terminate
      certificateRefs:
      - name: wildcard-tls-cert
    allowedRoutes:
      namespaces:
        from: All
</code></pre>

<h3>Example: Application HTTPRoute with Header Filters</h3>
<pre><code class="language-yaml">apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: orders-service-route
  namespace: e-commerce
spec:
  parentRefs:
  - name: shared-edge-gateway
    namespace: gateway-system
  hostnames:
  - "api.example.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /orders
    filters:
    - type: RequestHeaderModifier
      requestHeaderModifier:
        set:
        - name: X-Forwarded-Gateway
          value: Gateway-API-Production
    backendRefs:
    - name: orders-service
      port: 8080
      weight: 100
</code></pre>

<h2>Zero-Downtime Validation and Cutover Strategy</h2>
<p>Migrating production ingress requires an airtight, zero-downtime execution strategy. The recommended operational workflow follows a parallel dual-stack deployment:</p>
<ol>
    <li><strong>Deploy the New Controller:</strong> Install the target Gateway API controller (such as NGINX Gateway Fabric or Envoy Gateway) alongside the existing <code>ingress-nginx</code> installation.</li>
    <li><strong>Pre-Cutover Route Verification:</strong> Before altering DNS records, validate routing, TLS termination, and header filters by issuing HTTP requests directly against the new Gateway LoadBalancer IP using <code>curl --resolve</code>:
        <pre><code class="language-bash">curl -iv --resolve api.example.com:443:&lt;GATEWAY_LB_IP&gt; https://api.example.com/orders/health</code></pre>
    </li>
    <li><strong>Weighted Canary DNS Shift:</strong> Utilize Route53 or Cloudflare weighted DNS records to shift 5% of incoming traffic to the Gateway API endpoint. Monitor latency metrics, 5xx error spikes, and access logs.</li>
    <li><strong>Full Cutover &amp; Decommissioning:</strong> Once the traffic shift reaches 100% and DNS TTLs elapse, safely delete legacy Ingress resources and uninstall the obsolete <code>ingress-nginx</code> Helm chart.</li>
</ol>

<h2>Verified References &amp; Further Reading</h2>
<ul>
    <li><a href="https://kubernetes.io/blog/2023/10/25/introducing-ingress2gateway/">Introducing ingress2gateway: Simplifying Upgrades to Gateway API</a> — Kubernetes Official Blog (SIG Network)</li>
    <li><a href="https://gateway-api.sigs.k8s.io/concepts/">Kubernetes Gateway API Architectural Concepts &amp; Specification</a> — Kubernetes SIG Network Documentation</li>
    <li><a href="https://github.com/kubernetes-sigs/ingress2gateway">kubernetes-sigs/ingress2gateway Migration CLI Repository</a> — GitHub</li>
    <li><a href="https://www.cncf.io/blog/2026/04/13/ingress-nginx-to-envoy-gateway-migration-on-cncf-internal-services-cluster/">Ingress-NGINX to Envoy Gateway Migration Case Study</a> — Cloud Native Computing Foundation (CNCF)</li>
    <li><a href="https://docs.nginx.com/nginx-gateway-fabric/installation/migrate-nic-ngf/">Migrating from NGINX Ingress Controller to NGINX Gateway Fabric</a> — F5 NGINX Documentation</li>
</ul>
"""

def run_real_pipeline():
    print("=== Step 1: Saving Article Draft to SQLite ===")
    save_res = save_article(
        topic_id=1,
        site_id=1,
        title="Migrating from Ingress-NGINX to Kubernetes Gateway API: A Production Migration Guide",
        slug="migrating-ingress-nginx-to-kubernetes-gateway-api",
        section="Cloud & DevOps",
        content_html=ARTICLE_HTML.strip(),
        meta_description="A comprehensive production migration guide from Ingress-NGINX to Kubernetes Gateway API covering ingress2gateway, architecture, TLS, and zero-downtime cutover.",
        change_summary="Complete production draft synthesized from 5 verified technical sources",
    )
    print("Article Save Result:", json.dumps(save_res, indent=2))
    article_id = save_res["article_id"]

    print("\n=== Step 2: Running Deterministic Validation Engine ===")
    val_res = validate_article(article_id=article_id)
    print("Validation Result:", json.dumps(val_res, indent=2))
    assert val_res["passed"] is True, f"Validation failed: {val_res['errors']}"
    assert val_res["new_status"] == "APPROVED"

    print("\n=== Step 3: Gated Publishing to WordPress (Safe Dry-Run Mode) ===")
    pub_res = publish_article(article_id=article_id, as_draft=True)
    print("Publication Result:", json.dumps(pub_res, indent=2))
    assert pub_res["status"] == "success"

    print("\n=== Step 4: Verifying Publication Status ===")
    ver_res = verify_publication(article_id=article_id)
    print("Verification Result:", json.dumps(ver_res, indent=2))
    assert ver_res["status"] == "verified"

    print("\n=== Step 5: Final SQLite State Audit ===")
    summary = db.get_pipeline_summary()
    print("Final Pipeline Summary in SQLite:", json.dumps(summary, indent=2))

    article_row = db.get_article(article_id)
    print(f"\nFinal Article State: ID={article_row['id']} Status='{article_row['status']}' Version={article_row['version_num']}")
    print(f"Publication Link: {pub_res.get('remote_url')}")


if __name__ == "__main__":
    run_real_pipeline()
