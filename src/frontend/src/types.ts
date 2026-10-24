// Types mirror the JSON contracts in docs/working/03-analysis-design.md section 8.
export interface ApiErrorBody { error: { code: string; message: string; details?: Record<string, unknown> } }

export interface Health { status: string; run_id: string; uptime_s: number }
export interface ComponentInfo { id: string; label: string; weight: number }
export interface Meta {
  schema_version: number; run_id: string; git_commit: string; freeze_tag: string | null;
  data_fingerprint: string; components: ComponentInfo[]; snapshot_grid: number[]; cutoffs?: number[];
}
export interface AssessmentInfo { type: string; day: number | null; weight: number | null }
export interface Presentation {
  id: string; role: 'dev' | 'confirm'; status: 'published' | 'locked'; length_days: number;
  snapshots: number[]; cutoffs?: number[]; registrations: number; label_ar?: string; assessments?: AssessmentInfo[];
}
export interface RegistrationSummary {
  registration: string; id_student: number; date_registration: number;
  date_unregistration?: number | null; status?: string;
}
export interface Page<T> { items: T[]; total: number; limit: number; offset: number }

export interface NextAssessment { type: string; day: number; days_ahead: number }
export interface RecContext { week: number; next_assessment: NextAssessment | null; active_days_to_date: number }
export interface RecItem {
  rank: number; id_site: number; activity_type: string; score: number;
  contributions: Record<string, number>; reason: string; reason_secondary: string | null;
}
export interface Provenance { run_id: string; role: string; model_cut?: number | null }
export type RecStatus = 'ok' | 'no_history' | 'withdrawn';
export interface RecommendationResponse {
  registration: string; presentation: string; requested_day: number; snapshot_day: number;
  task: 'A' | 'B'; status: RecStatus; context: RecContext; components: ComponentInfo[];
  items: RecItem[]; provenance: Provenance;
}
export type Evidence =
  | { type: 'count'; n: number; window: number }
  | { type: 'item'; id_site: number; activity_type: string; days: number; last_day: number }
  | { type: 'assessment'; assessment_type: string; days_ahead: number };
export interface ExplComponent {
  id: string; label?: string; weight: number; r_tilde: number; contribution: number;
  evidence: Evidence | null; sentence: string;
}
export interface ExplanationDetail {
  registration: string; id_site: number; activity_type: string; task: string; day: number;
  snapshot_day: number; score: number; components: ExplComponent[]; notes?: string[];
}
export interface HistoryEvent { day: number; id_site: number; activity_type: string; clicks: number }
export interface LearnerHistory {
  registration: string; day: number; window: number; active_days: number;
  daily: { day: number; clicks: number }[]; recent: HistoryEvent[];
}

export interface RiskRow {
  score: number; cut_day: number; threshold: number; above_threshold: boolean;
  provenance: string; top_factor: string;
}
export interface ClusterRef { id: number; label: string }
export interface InstructorLearnerRow {
  registration: string; cluster: ClusterRef; active_days: number; last_access_day: number | null;
  on_time: string; risk: RiskRow | null;
}
export interface InstructorOverview {
  presentation: string; requested_day: number; snapshot_day: number;
  kpis: { active_learners: number; cohort_size?: number; median_active_days: number; catalogue_size: number; coverage_at_10: number; share_above_threshold: number | null };
  profile_summary: { name: string; p25: number; median: number; p75: number; unit: string }[];
  risk: { cut_day: number; threshold: number; provenance: string; label_ar?: string; histogram: { lo: number; hi: number; count: number }[] } | null;
  coverage: { at_10: number; catalogue_size: number; covered_items: number; by_type: { activity_type: string; catalogue_share: number; recs_share: number }[] };
  provenance: Provenance;
}
export interface ClusterSet {
  presentation: string; requested_day: number; snapshot_day: number; k: number; unstable: boolean; unstable_reason?: string | null; cluster_day?: number;
  quality: { silhouette: number; dbi: number; ari: number | null };
  clusters: { id: number; label_ar: string; size: number; top_features: { name: string; z: number }[] }[];
  points: { x: number; y: number; cluster: number }[];
}
export interface InstructorLearnerDetail {
  registration: string; day: number; snapshot_day: number; cluster: ClusterRef;
  risk: (RiskRow & { factors: { name: string; wz: number }[] }) | null;
  profile: { name: string; value: number; median: number; z: number }[];
  top_recs: { rank: number; id_site: number; activity_type: string; reason: string }[];
  withdrawn_day: number | null; outcome: unknown;
}
export type LearnerQuery = {
  presentation: string; day: number; cluster?: number; risk?: 'all' | 'above'; sort?: string; limit?: number; offset?: number;
};
