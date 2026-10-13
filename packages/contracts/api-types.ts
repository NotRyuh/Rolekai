// Generated from Rolekai OpenAPI. Run contracts:export; do not edit.
export interface components {
  "ActivityEvent": { "actor_type": "human" | "system"; "correlation_id": string; "event_type": string; "id": string; "metadata_json"?: { [key: string]: unknown; }; "occurred_at": string; "owner_id": string; "subject_id": string; "subject_type": "job" | "application" | "profile" | "evidence" | "evaluation"; };
  "ActivityPage": { "items": Array<components["ActivityEvent"]>; "next_cursor"?: (string | null); };
  "Application": { "application_url"?: (string | null); "applied_at"?: (string | null); "channel"?: (string | null); "created_at"?: string; "id": string; "job_id": string; "notes"?: (string | null); "owner_id": string; "status": components["ApplicationStatus"]; "updated_at"?: string; };
  "ApplicationCreate": { "application_url"?: (string | null); "applied_at"?: (string | null); "channel"?: (string | null); "confirmed": boolean; "notes"?: (string | null); "status"?: components["ApplicationStatus"]; };
  "ApplicationPatch": { "applied_at"?: (string | null); "channel"?: (string | null); "confirmed"?: boolean; "notes"?: (string | null); "status"?: (components["ApplicationStatus"] | null); };
  "ApplicationStatus": "preparing" | "applied" | "interviewing" | "offer" | "rejected" | "withdrawn" | "closed_unknown";
  "DecisionChange": { "decision_status": components["DecisionStatus"]; "reason"?: (string | null); };
  "DecisionStatus": "inbox" | "saved" | "dismissed";
  "DiscoveryStatus": "new" | "imported" | "normalized" | "duplicate_candidate" | "merged" | "archived" | "unavailable" | "unknown_availability";
  "Eligibility": "eligible" | "ineligible" | "unknown" | "needs_review";
  "ErrorDetail": { "code": string; "details"?: Array<string>; "message": string; "request_id": string; };
  "ErrorResponse": { "error": components["ErrorDetail"]; };
  "Evaluation": { "completed_at"?: (string | null); "created_at"?: string; "evidence"?: Array<components["EvidenceSpan"]>; "fit_score_relative"?: (number | null); "id": string; "job_id": string; "job_snapshot_hash": string; "model_config_data"?: { [key: string]: unknown; }; "owner_id": string; "profile_snapshot_hash": string; "prompt_version": string; "requirements"?: Array<components["EvaluationItem"]>; "score_breakdown_json"?: { [key: string]: unknown; }; "status"?: components["EvaluationStatus"]; "summary"?: (string | null); "unknowns"?: Array<string>; };
  "EvaluationAccepted": { "evaluation_id": string; "status"?: "queued"; };
  "EvaluationItem": { "classification": string; "confidence"?: (number | null); "evidence": Array<components["EvidenceSpan"]>; "priority": components["RuleStrength"]; "profile_evidence_id"?: (string | null); "reason": string; "requirement": string; "result": "covered" | "missing" | "unknown" | "conflicting"; };
  "EvaluationStatus": "not_queued" | "queued" | "evaluating" | "evaluated" | "needs_review" | "failed";
  "EvaluationSummary": { "fit_score_relative"?: (number | null); "id": string; "status": string; };
  "EvidenceCreate": { "evidence_date": string; "kind"?: "user_written"; "source": string; "text": string; };
  "EvidencePage": { "items": Array<components["ProfileEvidence"]>; "next_cursor"?: (string | null); };
  "EvidenceSpan": { "observation_id": string; "quote": string; };
  "FieldProvenance": { "citation"?: (string | null); "confidence"?: (number | null); "field_name": string; "id": string; "job_id": string; "observation_id": string; "payload_path"?: (string | null); "provenance_type": "source" | "rule" | "human" | "llm"; };
  "ImportAccepted": { "run_id": string; "source": components["SourceType"]; "status"?: "queued"; "submitted_at": string; };
  "ImportRequest": { "board"?: (string | null); "query"?: (string | null); "text"?: (string | null); "url"?: (string | null); };
  "ImportRun": { "created"?: number; "duplicate"?: number; "errors"?: Array<components["ErrorDetail"]>; "failed"?: number; "job_ids"?: Array<string>; "needs_review"?: number; "run_id": string; "source": components["SourceType"]; "status": "queued" | "running" | "completed" | "failed"; "updated"?: number; };
  "JobDetail": { "application"?: (components["Application"] | null); "apply_url"?: (string | null); "availability_status"?: "available" | "unavailable" | "unknown"; "canonical_url"?: (string | null); "company_display_name"?: (string | null); "company_key"?: (string | null); "country"?: (string | null); "created_at"?: string; "decision_status"?: components["DecisionStatus"]; "discovered_at"?: string; "discovery_status"?: components["DiscoveryStatus"]; "eligibility_reason"?: (string | null); "evaluations"?: Array<components["Evaluation"]>; "id": string; "last_verified_at"?: (string | null); "latest_evaluation"?: (components["EvaluationSummary"] | null); "merge_candidate_ids"?: Array<string>; "observations"?: Array<components["SourceObservation"]>; "owner_id": string; "posted_at"?: (string | null); "preferred_source"?: (components["SourceType"] | null); "provenance"?: Array<components["FieldProvenance"]>; "remote_eligibility"?: components["Eligibility"]; "salary"?: (string | null); "title_normalized"?: (string | null); "title_raw": string; "updated_at"?: string; "workplace_type"?: components["Workplace"]; };
  "JobListPage": { "items": Array<components["JobSummary"]>; "next_cursor"?: (string | null); };
  "JobSummary": { "apply_url"?: (string | null); "availability_status"?: "available" | "unavailable" | "unknown"; "canonical_url"?: (string | null); "company_display_name"?: (string | null); "company_key"?: (string | null); "country"?: (string | null); "created_at"?: string; "decision_status"?: components["DecisionStatus"]; "discovered_at"?: string; "discovery_status"?: components["DiscoveryStatus"]; "eligibility_reason"?: (string | null); "id": string; "last_verified_at"?: (string | null); "latest_evaluation"?: (components["EvaluationSummary"] | null); "owner_id": string; "posted_at"?: (string | null); "preferred_source"?: (components["SourceType"] | null); "remote_eligibility"?: components["Eligibility"]; "salary"?: (string | null); "title_normalized"?: (string | null); "title_raw": string; "updated_at"?: string; "workplace_type"?: components["Workplace"]; };
  "ProfileEvidence": { "evidence_date": string; "id": string; "kind"?: "user_written"; "owner_id": string; "source": string; "text": string; };
  "RuleStrength": "mandatory" | "preferred" | "informative";
  "SearchProfile": { "currency"?: (string | null); "exclusions"?: Array<string>; "languages"?: Array<string>; "location_strength"?: components["RuleStrength"]; "residence_country"?: string; "salary_min"?: (number | null); "technologies"?: Array<components["TechnologyPreference"]>; "title_strength"?: components["RuleStrength"]; "titles": Array<string>; "workplace"?: components["Workplace"]; "workplace_strength"?: components["RuleStrength"]; };
  "SourceObservation": { "attribution"?: (string | null); "content_hash": string; "external_id"?: (string | null); "id": string; "import_run_id"?: (string | null); "job_id": string; "original_description_html"?: (string | null); "original_description_text"?: (string | null); "owner_id": string; "parser_version": string; "raw_payload_json"?: { [key: string]: unknown; }; "retrieved_at": string; "source_type": components["SourceType"]; "source_updated_at"?: (string | null); "source_url"?: (string | null); };
  "SourceType": "manual" | "remotive" | "greenhouse";
  "TechnologyPreference": { "strength"?: components["RuleStrength"]; "value": string; };
  "Workplace": "remote" | "hybrid" | "onsite" | "unknown";
}

export interface paths {
  "/api/v1/activity": {
    "get": {
      query: { "cursor"?: (string | null); "event_type"?: (string | null); "limit"?: number; "subject_id"?: (string | null); };
      responses: {
        "200": components["ActivityPage"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
  };
  "/api/v1/applications/{app_id}": {
    "patch": {
      path: { "app_id": string; };
      body: components["ApplicationPatch"];
      responses: {
        "200": components["Application"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
  };
  "/api/v1/evaluations/{evaluation_id}": {
    "get": {
      path: { "evaluation_id": string; };
      responses: {
        "200": components["Evaluation"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
  };
  "/api/v1/import-runs/{run_id}": {
    "get": {
      path: { "run_id": string; };
      responses: {
        "200": components["ImportRun"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
  };
  "/api/v1/imports/greenhouse": {
    "post": {
      header: { "Idempotency-Key": string; };
      body: components["ImportRequest"];
      responses: {
        "202": components["ImportAccepted"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
  };
  "/api/v1/imports/remotive": {
    "post": {
      header: { "Idempotency-Key": string; };
      body: components["ImportRequest"];
      responses: {
        "202": components["ImportAccepted"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
  };
  "/api/v1/imports/url": {
    "post": {
      header: { "Idempotency-Key": string; };
      body: components["ImportRequest"];
      responses: {
        "202": components["ImportAccepted"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
  };
  "/api/v1/jobs": {
    "get": {
      query: { "cursor"?: (string | null); "decision_status"?: (components["DecisionStatus"] | null); "limit"?: number; "posted_after"?: (string | null); "posted_before"?: (string | null); "remote_eligibility"?: (components["Eligibility"] | null); "source"?: (components["SourceType"] | null); };
      responses: {
        "200": components["JobListPage"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
  };
  "/api/v1/jobs/{job_id}": {
    "get": {
      path: { "job_id": string; };
      responses: {
        "200": components["JobDetail"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
  };
  "/api/v1/jobs/{job_id}/applications": {
    "post": {
      path: { "job_id": string; };
      body: components["ApplicationCreate"];
      responses: {
        "201": components["Application"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
  };
  "/api/v1/jobs/{job_id}/decision": {
    "patch": {
      path: { "job_id": string; };
      body: components["DecisionChange"];
      responses: {
        "200": components["JobSummary"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
  };
  "/api/v1/jobs/{job_id}/evaluations": {
    "post": {
      path: { "job_id": string; };
      header: { "Idempotency-Key": string; };
      responses: {
        "202": components["EvaluationAccepted"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
  };
  "/api/v1/profile/evidence": {
    "get": {
      query: { "cursor"?: (string | null); "limit"?: number; };
      responses: {
        "200": components["EvidencePage"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
    "post": {
      body: components["EvidenceCreate"];
      responses: {
        "201": components["ProfileEvidence"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
  };
  "/api/v1/profile/search": {
    "get": {
      responses: {
        "200": components["SearchProfile"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
    "put": {
      body: components["SearchProfile"];
      responses: {
        "200": components["SearchProfile"];
        "401": components["ErrorResponse"];
        "404": components["ErrorResponse"];
        "409": components["ErrorResponse"];
        "422": components["ErrorResponse"];
        "503": components["ErrorResponse"];
      };
    };
  };
  "/health/live": {
    "get": {
      responses: {
        "200": { [key: string]: string; };
      };
    };
  };
  "/health/ready": {
    "get": {
      responses: {
        "200": unknown;
        "503": unknown;
      };
    };
  };
}
