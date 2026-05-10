import time
from app.core.llm import get_llm
from app.core.memory import get_memory
from app.agents.tools import tool_search_documents, tool_analyze_findings, tool_synthesize_answer, tool_verify_answer
from app.models.schemas import AgentStep, AgentRole, QueryComplexity, QueryResponse, Citation, MessageRole


class AgentOrchestrator:
    def __init__(self, workspace: str = "default"):
        self.workspace = workspace
        self.llm = get_llm()
        self.memory = get_memory()

    async def run(self, question: str, conversation_id: str | None = None, stream: bool = False) -> QueryResponse:
        start_time = time.time()
        trace: list[AgentStep] = []
        if not conversation_id:
            conversation_id = self.memory.create(self.workspace)
        conv = self.memory.get(conversation_id)
        if not conv:
            conversation_id = self.memory.create(self.workspace)

        # Step 1: Classify (no API call - rule-based)
        t0 = time.time()
        complexity_str = self.llm.classify_complexity(question)
        try:
            complexity = QueryComplexity(complexity_str)
        except ValueError:
            complexity = QueryComplexity.MODERATE
        trace.append(AgentStep(agent=AgentRole.ORCHESTRATOR, action="classify", thought="Classifying query complexity...", result=f"Complexity: {complexity.value}", latency_ms=(time.time() - t0) * 1000))

        # Step 2: Plan
        plan = self._plan_agents(complexity)
        trace.append(AgentStep(agent=AgentRole.ORCHESTRATOR, action="plan", thought=f"Query is {complexity.value}, planning pipeline", result=f"Pipeline: {' -> '.join(plan)}", latency_ms=0))

        # Step 3: Research
        t0 = time.time()
        search_result = await tool_search_documents(question, self.workspace)
        chunks = search_result["chunks"]
        trace.append(AgentStep(agent=AgentRole.RESEARCHER, action="search", thought="Searching knowledge base...", result=f"Found {len(chunks)} relevant chunks", latency_ms=search_result["latency_ms"]))

        if not chunks:
            return QueryResponse(answer="No relevant information found in the knowledge base.", citations=[], agent_trace=trace, complexity=complexity, total_latency_ms=(time.time() - start_time) * 1000, documents_searched=0, chunks_retrieved=0, model_used=self.llm.settings.llm_model, conversation_id=conversation_id, confidence_score=0.0)

        # Step 4: Analyze
        analysis = {}
        if "analyze" in plan:
            t0 = time.time()
            try:
                analysis = await tool_analyze_findings(question, chunks)
                trace.append(AgentStep(agent=AgentRole.ANALYST, action="analyze", thought="Extracting key facts and gaps...", result=f"Facts: {len(analysis.get('key_facts', []))} | Gaps: {len(analysis.get('gaps', []))} | Confidence: {analysis.get('confidence', 0)}", latency_ms=analysis.get("latency_ms", 0)))
            except Exception as e:
                trace.append(AgentStep(agent=AgentRole.ANALYST, action="analyze", thought="Analysis step", result=f"Skipped due to rate limit", latency_ms=0))

        # Step 5: Synthesize
        t0 = time.time()
        try:
            synth_result = await tool_synthesize_answer(question, chunks, analysis)
            answer = synth_result["answer"]
            confidence = synth_result.get("confidence", 0.5)
            trace.append(AgentStep(agent=AgentRole.SYNTHESIZER, action="synthesize", thought="Composing answer with citations...", result=f"Answer generated ({len(answer)} chars)", latency_ms=synth_result.get("latency_ms", 0)))
        except Exception as e:
            # Fallback: direct RAG answer without extra LLM calls
            answer = self._fallback_answer(chunks, question)
            confidence = 0.4
            trace.append(AgentStep(agent=AgentRole.SYNTHESIZER, action="synthesize", thought="Fallback synthesis", result=f"Used fallback ({len(answer)} chars)", latency_ms=(time.time() - t0) * 1000))

        # Step 6: Verify (only for complex/analytical, skip if rate limited)
        if "verify" in plan:
            try:
                t0 = time.time()
                verify_result = await tool_verify_answer(question, answer, chunks)
                if not verify_result.get("verified", True):
                    fix = verify_result.get("suggested_fix", "")
                    if fix:
                        answer += f"\n\n**Verification Note:** {fix}"
                    confidence *= verify_result.get("accuracy_score", 0.8)
                trace.append(AgentStep(agent=AgentRole.VERIFIER, action="verify", thought="Fact-checking...", result=f"Verified: {verify_result.get('verified', True)} | Accuracy: {verify_result.get('accuracy_score', 0):.2f}", latency_ms=verify_result.get("latency_ms", 0)))
            except Exception:
                trace.append(AgentStep(agent=AgentRole.VERIFIER, action="verify", thought="Verify step", result="Skipped due to rate limit", latency_ms=0))

        citations = [Citation(source_file=c["source"], chunk_text=c["text"][:200] + "...", relevance_score=c["score"], chunk_index=c["chunk_index"]) for c in chunks[:6]]
        self.memory.add_message(conversation_id, MessageRole.USER, question)
        self.memory.add_message(conversation_id, MessageRole.ASSISTANT, answer)
        total_latency = (time.time() - start_time) * 1000

        return QueryResponse(answer=answer, citations=citations, agent_trace=trace, complexity=complexity, total_latency_ms=total_latency, documents_searched=len(set(c["source"] for c in chunks)), chunks_retrieved=len(chunks), model_used=self.llm.settings.llm_model, conversation_id=conversation_id, confidence_score=round(confidence, 3))

    def _plan_agents(self, complexity: QueryComplexity) -> list[str]:
        plans = {
            QueryComplexity.SIMPLE: ["search", "synthesize"],
            QueryComplexity.MODERATE: ["search", "analyze", "synthesize"],
            QueryComplexity.COMPLEX: ["search", "analyze", "synthesize", "verify"],
            QueryComplexity.ANALYTICAL: ["search", "analyze", "synthesize", "verify"],
        }
        return plans.get(complexity, plans[QueryComplexity.MODERATE])

    def _fallback_answer(self, chunks: list[dict], question: str) -> str:
        sources = {}
        for c in chunks[:4]:
            src = c["source"]
            if src not in sources:
                sources[src] = []
            sources[src].append(c["text"])
        answer_parts = [f"Based on the knowledge base:\n"]
        for src, texts in sources.items():
            answer_parts.append(f"**From {src}:**\n" + "\n".join(texts[:2]))
            answer_parts.append("")
        return "\n".join(answer_parts)
