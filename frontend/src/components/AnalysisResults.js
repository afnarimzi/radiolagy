import React, { useState } from 'react';
import {
  FileText, Activity, BookOpen, AlertTriangle, Award,
  ChevronDown, ChevronUp, CheckCircle, XCircle, RefreshCw,
  Layers, Shield, BarChart2
} from 'lucide-react';

// ── helpers ──────────────────────────────────────────────────────────────────

const pct = (v) => (v != null ? `${Math.round(v * 100)}%` : 'N/A');
const pct100 = (v) => (v != null ? `${Math.round(v)}%` : 'N/A');

const ConfidenceBar = ({ value }) => {
  const p = Math.round((value || 0) * 100);
  const color = p >= 80 ? 'bg-green-500' : p >= 60 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-1 bg-gray-200 rounded-full h-2">
        <div className={`${color} h-2 rounded-full`} style={{ width: `${p}%` }} />
      </div>
      <span className="text-sm font-medium text-gray-700 w-10 text-right">{p}%</span>
    </div>
  );
};

const Badge = ({ label, color }) => {
  const colors = {
    green:  'bg-green-100 text-green-800',
    red:    'bg-red-100 text-red-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    blue:   'bg-blue-100 text-blue-800',
    gray:   'bg-gray-100 text-gray-700',
    purple: 'bg-purple-100 text-purple-800',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${colors[color] || colors.gray}`}>
      {label}
    </span>
  );
};

const Section = ({ icon: Icon, title, color = 'blue', children, defaultOpen = false }) => {
  const [open, setOpen] = useState(defaultOpen);
  const colors = {
    blue:   'bg-blue-50 border-blue-200 text-blue-700',
    green:  'bg-green-50 border-green-200 text-green-700',
    purple: 'bg-purple-50 border-purple-200 text-purple-700',
    orange: 'bg-orange-50 border-orange-200 text-orange-700',
    red:    'bg-red-50 border-red-200 text-red-700',
    teal:   'bg-teal-50 border-teal-200 text-teal-700',
  };
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className={`w-full flex items-center justify-between p-4 ${colors[color]} border-b`}
      >
        <div className="flex items-center gap-2 font-semibold text-base">
          <Icon className="w-5 h-5" />
          {title}
        </div>
        {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>
      {open && <div className="p-5">{children}</div>}
    </div>
  );
};

// ── Dual-model section ────────────────────────────────────────────────────────

const DecisionIcon = ({ decision }) => {
  if (decision === 'PASS') return <CheckCircle className="w-6 h-6 text-green-600" />;
  if (decision === 'FAIL') return <XCircle className="w-6 h-6 text-red-600" />;
  return <RefreshCw className="w-6 h-6 text-yellow-600" />;
};

const decisionBadge = (d) =>
  d === 'PASS' ? 'green' : d === 'FAIL' ? 'red' : 'yellow';

const MetricRow = ({ label, value }) => (
  <div className="flex justify-between items-center py-1.5 border-b border-gray-100 last:border-0">
    <span className="text-sm text-gray-600">{label}</span>
    <span className="text-sm font-semibold text-gray-800">{value}</span>
  </div>
);

const DualRadiologySection = ({ dual }) => {
  if (!dual) return null;

  const { gemini_output, groq_output, validation_result, consensus_metrics, final_decision, decision_reasoning, retry_count } = dual;
  const vm = validation_result || {};
  const cm = consensus_metrics || {};

  return (
    <Section icon={Layers} title="Dual-Model Validation (Gemini + Groq)" color="purple" defaultOpen={true}>
      {/* Decision banner */}
      <div className={`flex items-center gap-3 p-4 rounded-lg mb-5 ${
        final_decision === 'PASS' ? 'bg-green-50 border border-green-200' :
        final_decision === 'FAIL' ? 'bg-red-50 border border-red-200' :
        'bg-yellow-50 border border-yellow-200'
      }`}>
        <DecisionIcon decision={final_decision} />
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-gray-900">Validation Decision:</span>
            <Badge label={final_decision || 'UNKNOWN'} color={decisionBadge(final_decision)} />
            {retry_count > 0 && <Badge label={`${retry_count} retry`} color="yellow" />}
          </div>
          {decision_reasoning && (
            <p className="text-sm text-gray-600 mt-1">{decision_reasoning}</p>
          )}
        </div>
      </div>

      {/* Two model outputs side by side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
        {/* Gemini */}
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
          <div className="flex items-center gap-2 mb-3">
            <Badge label="Gemini Vision" color="blue" />
            <span className="text-xs text-gray-500">{gemini_output?.model_name}</span>
          </div>
          <div className="text-sm text-gray-700 mb-2 line-clamp-4">{gemini_output?.findings || '—'}</div>
          <div className="text-xs text-gray-500 mb-1">Confidence</div>
          <ConfidenceBar value={gemini_output?.confidence} />
          <div className="mt-2 text-xs text-gray-500">Quality: <span className="font-medium">{gemini_output?.image_quality || '—'}</span></div>
          {gemini_output?.abnormalities?.length > 0 && (
            <div className="mt-2">
              <div className="text-xs text-gray-500 mb-1">Abnormalities</div>
              <div className="flex flex-wrap gap-1">
                {gemini_output.abnormalities.map((a, i) => <Badge key={i} label={a} color="blue" />)}
              </div>
            </div>
          )}
        </div>

        {/* Groq */}
        <div className="bg-purple-50 rounded-lg p-4 border border-purple-100">
          <div className="flex items-center gap-2 mb-3">
            <Badge label="Groq Llama" color="purple" />
            <span className="text-xs text-gray-500">{groq_output?.model_name}</span>
          </div>
          <div className="text-sm text-gray-700 mb-2 line-clamp-4">{groq_output?.findings || '—'}</div>
          <div className="text-xs text-gray-500 mb-1">Confidence</div>
          <ConfidenceBar value={groq_output?.confidence} />
          <div className="mt-2 text-xs text-gray-500">Quality: <span className="font-medium">{groq_output?.image_quality || '—'}</span></div>
          {groq_output?.abnormalities?.length > 0 && (
            <div className="mt-2">
              <div className="text-xs text-gray-500 mb-1">Abnormalities</div>
              <div className="flex flex-wrap gap-1">
                {groq_output.abnormalities.map((a, i) => <Badge key={i} label={a} color="purple" />)}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Consensus metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="flex items-center gap-2 mb-3 font-semibold text-gray-700">
            <BarChart2 className="w-4 h-4" /> Consensus Metrics
          </div>
          <MetricRow label="Overall Consensus Score" value={pct(vm.consensus_score)} />
          <MetricRow label="Cohen's Kappa (κ)" value={cm.cohens_kappa != null ? cm.cohens_kappa.toFixed(3) : 'N/A'} />
          <MetricRow label="Semantic Similarity" value={pct(cm.semantic_similarity_score)} />
          <MetricRow label="Abnormality Overlap" value={pct(cm.abnormality_overlap_ratio)} />
          <MetricRow label="Exact Match" value={pct100(cm.exact_match_percentage)} />
          <MetricRow label="Clinical Alignment" value={pct(cm.clinical_significance_alignment)} />
          <MetricRow label="Quality Agreement" value={cm.quality_agreement ? '✅ Yes' : '❌ No'} />
        </div>

        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="flex items-center gap-2 mb-3 font-semibold text-gray-700">
            <Shield className="w-4 h-4" /> Validation Checks
          </div>
          <MetricRow label="Confidence Threshold" value={vm.confidence_validation ? '✅ Pass' : '❌ Fail'} />
          <MetricRow label="Quality Threshold" value={vm.quality_validation ? '✅ Pass' : '❌ Fail'} />
          <MetricRow label="Critical Findings Match" value={vm.critical_findings_match ? '✅ Match' : '❌ Mismatch'} />
          <MetricRow label="Abnormality Agreement" value={pct(vm.abnormality_agreement)} />
          {vm.discrepancies?.length > 0 && (
            <div className="mt-3">
              <div className="text-xs font-semibold text-red-600 mb-1">Discrepancies</div>
              {vm.discrepancies.map((d, i) => (
                <div key={i} className="text-xs text-red-700 bg-red-50 rounded p-1.5 mb-1">{d}</div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Section>
  );
};

// ── Main component ────────────────────────────────────────────────────────────

const AnalysisResults = ({ results }) => {
  if (!results) return null;

  const {
    radiology_analysis: rad = {},
    clinical_analysis: clin = {},
    evidence_research: ev = {},
    risk_assessment: risk = {},
    chairman_report: chair = {},
    dual_radiology_findings: dual,
  } = results;

  const riskColor = { low: 'green', medium: 'yellow', high: 'red', critical: 'red' };

  return (
    <div className="space-y-4">

      {/* Dual-model section — shown first when available */}
      {dual && <DualRadiologySection dual={dual} />}

      {/* Radiology */}
      <Section icon={FileText} title="Radiology Analysis" color="blue" defaultOpen={!dual}>
        <p className="text-sm text-gray-700 mb-4">{rad.findings || 'No findings'}</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="font-medium text-gray-700 mb-2">Abnormalities</div>
            {rad.abnormalities?.length > 0
              ? <ul className="list-disc list-inside space-y-1">{rad.abnormalities.map((a, i) => <li key={i} className="text-sm text-gray-600">{a}</li>)}</ul>
              : <span className="text-sm text-gray-400">None detected</span>}
          </div>
          <div>
            <div className="font-medium text-gray-700 mb-1">Image Quality</div>
            <Badge label={rad.image_quality || 'unknown'} color="blue" />
            <div className="font-medium text-gray-700 mt-3 mb-1">Confidence</div>
            <ConfidenceBar value={rad.confidence} />
          </div>
        </div>
      </Section>

      {/* Clinical */}
      <Section icon={Activity} title="Clinical Analysis" color="green">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="font-medium text-gray-700 mb-2">Differential Diagnosis</div>
            {(Array.isArray(clin.differential_diagnosis) ? clin.differential_diagnosis : [clin.differential_diagnosis]).filter(Boolean).map((d, i) => (
              <div key={i} className="text-sm text-gray-600 py-1 border-b border-gray-100">{d}</div>
            ))}
          </div>
          <div>
            <div className="font-medium text-gray-700 mb-1">Urgency</div>
            <Badge label={clin.urgency || 'unknown'} color={clin.urgency === 'high' ? 'red' : clin.urgency === 'medium' ? 'yellow' : 'green'} />
            <div className="font-medium text-gray-700 mt-3 mb-1">Confidence</div>
            <ConfidenceBar value={clin.confidence} />
          </div>
        </div>
        {clin.reasoning && (
          <div className="mt-4">
            <div className="font-medium text-gray-700 mb-1">Reasoning</div>
            <p className="text-sm text-gray-600">{clin.reasoning}</p>
          </div>
        )}
      </Section>

      {/* Risk */}
      <Section icon={AlertTriangle} title="Risk Assessment" color="orange">
        <div className="flex items-center gap-3 mb-4">
          <Badge label={`${(risk.risk_level || 'unknown').toUpperCase()} RISK`} color={riskColor[risk.risk_level?.toLowerCase()] || 'gray'} />
          <span className="text-sm text-gray-600">Score: <strong>{pct(risk.risk_score)}</strong></span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="font-medium text-gray-700 mb-1">Recommended Action</div>
            <p className="text-sm text-gray-600">{risk.recommended_action || '—'}</p>
            <div className="font-medium text-gray-700 mt-3 mb-1">Timeline</div>
            <p className="text-sm text-gray-600">{risk.urgency_timeline || '—'}</p>
          </div>
          <div>
            {risk.critical_findings?.length > 0 && (
              <>
                <div className="font-medium text-red-600 mb-1">Critical Findings</div>
                <ul className="list-disc list-inside space-y-1">{risk.critical_findings.map((f, i) => <li key={i} className="text-sm text-red-700">{f}</li>)}</ul>
              </>
            )}
          </div>
        </div>
      </Section>

      {/* Evidence */}
      <Section icon={BookOpen} title="Evidence Research" color="teal">
        <div className="flex items-center gap-3 mb-3">
          <span className="text-sm text-gray-600">Keywords: <strong>{ev.search_keywords || '—'}</strong></span>
          <Badge label={`${ev.total_papers_found || 0} papers`} color="blue" />
        </div>
        <p className="text-sm text-gray-700 mb-4">{ev.evidence_summary || 'No summary'}</p>
        {ev.citations?.length > 0 && (
          <div>
            <div className="font-medium text-gray-700 mb-2">Citations</div>
            {ev.citations.slice(0, 5).map((c, i) => (
              <div key={i} className="text-xs text-gray-600 py-1.5 border-b border-gray-100">
                <strong>{i + 1}.</strong>{' '}
                {c.url
                  ? <a href={c.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{c.title}</a>
                  : c.title
                }
                {' '}— {c.journal} ({c.year})
                {c.url && <span className="ml-2 text-blue-400 text-xs">[PubMed ↗]</span>}
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Chairman */}
      <Section icon={Award} title="Chairman Summary" color="red" defaultOpen={true}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="md:col-span-2">
            <div className="font-medium text-gray-700 mb-1">Primary Diagnosis</div>
            <p className="text-base font-semibold text-blue-700">{chair.primary_diagnosis || '—'}</p>
          </div>
          <div>
            <div className="font-medium text-gray-700 mb-1">Urgency</div>
            <Badge label={(chair.urgency_level || 'unknown').toUpperCase()} color={riskColor[chair.urgency_level?.toLowerCase()] || 'gray'} />
            <div className="font-medium text-gray-700 mt-3 mb-1">Confidence</div>
            <ConfidenceBar value={chair.confidence_level} />
          </div>
        </div>
        <div className="font-medium text-gray-700 mb-1">Executive Summary</div>
        <p className="text-sm text-gray-700 mb-4">{chair.executive_summary || '—'}</p>
        {chair.immediate_actions?.length > 0 && (
          <div>
            <div className="font-medium text-gray-700 mb-2">Immediate Actions</div>
            <ul className="space-y-1">{chair.immediate_actions.map((a, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />{a}
              </li>
            ))}</ul>
          </div>
        )}
      </Section>
    </div>
  );
};

export default AnalysisResults;
