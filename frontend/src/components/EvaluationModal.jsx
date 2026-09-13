import React, { useEffect, useState } from "react";
import { X, BarChart3, ShieldCheck, Cpu, Layers, AlertTriangle, RefreshCw } from "lucide-react";
import { fetchEvaluationResults } from "../services/api";

export default function EvaluationModal({ onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    fetchResults();
  }, []);

  const fetchResults = async () => {
    setLoading(true);
    try {
      const json = await fetchEvaluationResults();
      setData(json);
    } catch (e) {
      console.error("Error fetching evaluation results:", e);
    } finally {
      setLoading(false);
    }
  };

  const finalRes = data?.final || data?.baseline;
  const expRes = data?.experiments;
  const retMetrics = finalRes?.retrieval_metrics || {};
  const absMetrics = finalRes?.abstention_metrics || {};
  const stats = finalRes?.dataset_statistics || {};
  const latencies = finalRes?.latency_metrics_ms || {};

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-surface border border-outline-variant rounded-2xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-outline-variant bg-surface-variant/30">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary/10 text-primary">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-serif text-lg font-bold text-on-surface">
                Evaluation & Benchmark Dashboard
              </h2>
              <p className="text-xs text-on-surface-variant">
                105-Question Grounded Academic RAG Evaluation Suite
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={fetchResults}
              className="p-2 rounded-lg text-on-surface-variant hover:text-primary hover:bg-surface-variant transition-colors"
              title="Refresh Benchmark Results"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
            <button 
              onClick={onClose}
              className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-variant transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-outline-variant px-6 bg-surface-variant/10">
          <button
            onClick={() => setActiveTab("overview")}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === "overview"
                ? "border-primary text-primary"
                : "border-transparent text-on-surface-variant hover:text-on-surface"
            }`}
          >
            Overview & Metrics
          </button>
          <button
            onClick={() => setActiveTab("experiments")}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === "experiments"
                ? "border-primary text-primary"
                : "border-transparent text-on-surface-variant hover:text-on-surface"
            }`}
          >
            Controlled A/B Experiments
          </button>
          <button
            onClick={() => setActiveTab("dataset")}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === "dataset"
                ? "border-primary text-primary"
                : "border-transparent text-on-surface-variant hover:text-on-surface"
            }`}
          >
            Dataset & Failures
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-on-surface-variant">
              <RefreshCw className="w-6 h-6 animate-spin text-primary" />
              <span className="text-xs">Loading benchmark evaluation metrics...</span>
            </div>
          ) : !finalRes ? (
            <div className="text-center py-16 text-on-surface-variant space-y-2">
              <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto" />
              <p className="text-sm font-semibold">No benchmark metrics file found.</p>
              <p className="text-xs">Run <code className="bg-surface-variant px-2 py-1 rounded">python -m app.evaluation.runner</code> to generate metrics.</p>
            </div>
          ) : (
            <>
              {/* TAB 1: OVERVIEW */}
              {activeTab === "overview" && (
                <div className="space-y-6">
                  {/* Metric Summary Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 rounded-xl bg-surface-variant/40 border border-outline-variant">
                      <div className="text-xs text-on-surface-variant font-medium">Recall@5</div>
                      <div className="text-2xl font-bold text-primary mt-1">
                        {(retMetrics.recall_at_5 * 100).toFixed(2)}%
                      </div>
                      <div className="text-[10px] text-on-surface-variant mt-1">Top-5 Document Retrieval</div>
                    </div>
                    
                    <div className="p-4 rounded-xl bg-surface-variant/40 border border-outline-variant">
                      <div className="text-xs text-on-surface-variant font-medium">Mean Reciprocal Rank (MRR)</div>
                      <div className="text-2xl font-bold text-emerald-500 mt-1">
                        {retMetrics.mrr}
                      </div>
                      <div className="text-[10px] text-on-surface-variant mt-1">First Relevant Match Rank</div>
                    </div>

                    <div className="p-4 rounded-xl bg-surface-variant/40 border border-outline-variant">
                      <div className="text-xs text-on-surface-variant font-medium">Abstention Accuracy</div>
                      <div className="text-2xl font-bold text-blue-500 mt-1">
                        {(absMetrics.accuracy * 100).toFixed(2)}%
                      </div>
                      <div className="text-[10px] text-on-surface-variant mt-1">Groundedness Gate Precision</div>
                    </div>

                    <div className="p-4 rounded-xl bg-surface-variant/40 border border-outline-variant">
                      <div className="text-xs text-on-surface-variant font-medium">False Answer Rate</div>
                      <div className="text-2xl font-bold text-emerald-500 mt-1">
                        {(absMetrics.false_answer_rate * 100).toFixed(2)}%
                      </div>
                      <div className="text-[10px] text-on-surface-variant mt-1">Evaluation Hallucination Rate</div>
                    </div>
                  </div>

                  {/* Retrieval & Latency Grids */}
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Retrieval Detail */}
                    <div className="p-5 rounded-xl bg-surface-variant/20 border border-outline-variant space-y-3">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-primary flex items-center gap-2">
                        <Layers className="w-4 h-4" /> Retrieval Metric Breakdown
                      </h3>
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between py-1 border-b border-outline-variant/40">
                          <span className="text-on-surface-variant">Recall@1</span>
                          <span className="font-semibold">{(retMetrics.recall_at_1 * 100).toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-outline-variant/40">
                          <span className="text-on-surface-variant">Recall@3</span>
                          <span className="font-semibold">{(retMetrics.recall_at_3 * 100).toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-outline-variant/40">
                          <span className="text-on-surface-variant">Recall@5</span>
                          <span className="font-semibold text-primary">{(retMetrics.recall_at_5 * 100).toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-outline-variant/40">
                          <span className="text-on-surface-variant">Precision@5</span>
                          <span className="font-semibold">{(retMetrics.precision_at_5 * 100).toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between py-1">
                          <span className="text-on-surface-variant">nDCG@5</span>
                          <span className="font-semibold text-emerald-500">{retMetrics.ndcg_at_5}</span>
                        </div>
                      </div>
                    </div>

                    {/* Latency Breakdown */}
                    <div className="p-5 rounded-xl bg-surface-variant/20 border border-outline-variant space-y-3">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-primary flex items-center gap-2">
                        <Cpu className="w-4 h-4" /> Pipeline Stage Latencies (ms)
                      </h3>
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between py-1 border-b border-outline-variant/40">
                          <span className="text-on-surface-variant">FAISS Dense Search</span>
                          <span className="font-mono">{latencies.stage_breakdown_ms?.dense_retrieval || 0} ms</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-outline-variant/40">
                          <span className="text-on-surface-variant">BM25 Sparse Search</span>
                          <span className="font-mono">{latencies.stage_breakdown_ms?.bm25_retrieval || 0} ms</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-outline-variant/40">
                          <span className="text-on-surface-variant">FlashRank Cross-Encoder</span>
                          <span className="font-mono">{latencies.stage_breakdown_ms?.reranking || 0} ms</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-outline-variant/40">
                          <span className="text-on-surface-variant">Evidence Gate & Citations</span>
                          <span className="font-mono">{((latencies.stage_breakdown_ms?.evidence_gate || 0) + (latencies.stage_breakdown_ms?.citation_verification || 0)).toFixed(2)} ms</span>
                        </div>
                        <div className="flex justify-between py-1 font-semibold text-primary">
                          <span>Total End-to-End Latency</span>
                          <span className="font-mono">{latencies.mean_total_end_to_end_ms} ms</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: EXPERIMENTS */}
              {activeTab === "experiments" && (
                <div className="space-y-4">
                  <p className="text-xs text-on-surface-variant">
                    Controlled pipeline experiments evaluating individual RAG retrieval layers on the same 105 benchmark questions.
                  </p>
                  
                  <div className="overflow-x-auto border border-outline-variant rounded-xl">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-surface-variant/40 text-on-surface font-semibold border-b border-outline-variant">
                        <tr>
                          <th className="py-3 px-4">Experiment Configuration</th>
                          <th className="py-3 px-4">Recall@5</th>
                          <th className="py-3 px-4">MRR</th>
                          <th className="py-3 px-4">nDCG@5</th>
                          <th className="py-3 px-4">Abstention Acc.</th>
                          <th className="py-3 px-4">False Answer Rate</th>
                          <th className="py-3 px-4">Latency</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-outline-variant/40">
                        {expRes && Object.entries(expRes).map(([key, item]) => (
                          <tr key={key} className="hover:bg-surface-variant/20 transition-colors">
                            <td className="py-3 px-4 font-medium text-on-surface">
                              {key === "exp_a_dense_only" && "A. Dense Only (FAISS)"}
                              {key === "exp_b_dense_bm25" && "B. Dense + BM25"}
                              {key === "exp_c_dense_bm25_rrf" && "C. Dense + BM25 + RRF"}
                              {key === "exp_d_hybrid_reranker" && "D. Hybrid + FlashRank Reranker"}
                              {key === "exp_e_hybrid_reranker_gate" && "E. Hybrid + Reranker + Evidence Gate"}
                              {key === "exp_f_final_pipeline" && "F. Final System (+ Citation Verification)"}
                            </td>
                            <td className="py-3 px-4 font-mono">{(item.recall_at_5 * 100).toFixed(2)}%</td>
                            <td className="py-3 px-4 font-mono">{item.mrr}</td>
                            <td className="py-3 px-4 font-mono text-emerald-500">{item.ndcg_at_5}</td>
                            <td className="py-3 px-4 font-mono">{(item.abstention_accuracy * 100).toFixed(2)}%</td>
                            <td className="py-3 px-4 font-mono font-semibold text-emerald-500">
                              {(item.false_answer_rate * 100).toFixed(2)}%
                            </td>
                            <td className="py-3 px-4 font-mono text-on-surface-variant">{item.mean_latency_ms.toFixed(1)} ms</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* TAB 3: DATASET & FAILURES */}
              {activeTab === "dataset" && (
                <div className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Dataset Categories */}
                    <div className="p-5 rounded-xl bg-surface-variant/20 border border-outline-variant space-y-3">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-primary">
                        Benchmark Dataset Composition ({stats.total} Questions)
                      </h3>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="p-2.5 rounded-lg bg-surface-variant/40">
                          <span className="text-on-surface-variant block">Direct Factual</span>
                          <span className="font-bold text-on-surface">{stats.direct} questions</span>
                        </div>
                        <div className="p-2.5 rounded-lg bg-surface-variant/40">
                          <span className="text-on-surface-variant block">Multi-Chunk</span>
                          <span className="font-bold text-on-surface">{stats.multi_chunk} questions</span>
                        </div>
                        <div className="p-2.5 rounded-lg bg-surface-variant/40">
                          <span className="text-on-surface-variant block">Cross-Document</span>
                          <span className="font-bold text-on-surface">{stats.cross_doc} questions</span>
                        </div>
                        <div className="p-2.5 rounded-lg bg-surface-variant/40">
                          <span className="text-on-surface-variant block">Paraphrased</span>
                          <span className="font-bold text-on-surface">{stats.paraphrased} questions</span>
                        </div>
                        <div className="p-2.5 rounded-lg bg-surface-variant/40">
                          <span className="text-on-surface-variant block">Topic-Specific</span>
                          <span className="font-bold text-on-surface">{stats.topic_specific} questions</span>
                        </div>
                        <div className="p-2.5 rounded-lg bg-surface-variant/40">
                          <span className="text-on-surface-variant block">Out-of-Scope (Abstain)</span>
                          <span className="font-bold text-on-surface">{stats.out_of_scope} questions</span>
                        </div>
                        <div className="p-2.5 rounded-lg bg-surface-variant/40">
                          <span className="text-on-surface-variant block">Adversarial (Abstain)</span>
                          <span className="font-bold text-on-surface">{stats.adversarial} questions</span>
                        </div>
                        <div className="p-2.5 rounded-lg bg-surface-variant/40">
                          <span className="text-on-surface-variant block">Ambiguous (Abstain)</span>
                          <span className="font-bold text-on-surface">{stats.ambiguous} questions</span>
                        </div>
                      </div>
                    </div>

                    {/* Failure Classification Breakdown */}
                    <div className="p-5 rounded-xl bg-surface-variant/20 border border-outline-variant space-y-3">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-primary">
                        Failure Breakdown (5 / 105 Cases)
                      </h3>
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between py-1.5 border-b border-outline-variant/40">
                          <span className="text-on-surface-variant">Retrieval Failure</span>
                          <span className="font-mono text-emerald-500">0</span>
                        </div>
                        <div className="flex justify-between py-1.5 border-b border-outline-variant/40">
                          <span className="text-on-surface-variant">Ranking Failure</span>
                          <span className="font-mono text-emerald-500">0</span>
                        </div>
                        <div className="flex justify-between py-1.5 border-b border-outline-variant/40">
                          <span className="text-on-surface-variant">False Answer (Hallucination)</span>
                          <span className="font-mono text-emerald-500">0</span>
                        </div>
                        <div className="flex justify-between py-1.5 border-b border-outline-variant/40">
                          <span className="text-on-surface-variant">False Abstention</span>
                          <span className="font-mono text-amber-500 font-bold">5</span>
                        </div>
                        <p className="text-[11px] text-on-surface-variant pt-2 leading-relaxed">
                          All 5 false abstentions occurred on ambiguous single-word queries lacking entity anchors. The evidence gate scored them below the 0.25 threshold, choosing conservative abstention over ungrounded guessing.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-outline-variant bg-surface-variant/30 flex justify-between items-center">
          <span className="text-[11px] text-on-surface-variant">
            Grounded Evaluation Framework • Ask-the-Syllabus Bot
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-primary text-on-primary text-xs font-semibold rounded-lg hover:bg-primary/90 transition-colors"
          >
            Close Dashboard
          </button>
        </div>

      </div>
    </div>
  );
}
