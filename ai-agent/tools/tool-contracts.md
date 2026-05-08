# AI Agent Tool Contracts (13 Tools)

Specification for all 13 allowlisted tools with input/output schemas, authorization rules, and safety constraints.

---

## Tool Allowlist & Implementation Schedule

| # | Tool | Week | Auth | Type | Status |
|----|------|------|------|------|--------|
| 1 | search_certifications | W1 | All | Read | Pending |
| 2 | list_team_certs | W1 | Mgr,Aud | Read | Pending |
| 3 | check_compliance_gap | W1 | Mgr,Aud,Owner | Read | Pending |
| 4 | get_assignment_info | W2 | Mgr,Aud | Read | Pending |
| 5 | suggest_renewal_candidates | W2 | Mgr,Owner,Aud | Read | Pending |
| 6 | explain_validation_rules | W2 | Val,Aud | Read | Pending |
| 7 | list_available_waivers | W2 | Mgr,Owner | Read | Pending |
| 8 | get_certification_timeline | W2 | All | Read | Pending |
| 9 | estimate_coverage_impact | W2 | Mgr,Owner,Aud | Read | Pending |
| 10 | suggest_equivalent_certs | W2 | All | Read | Pending |
| 11 | prepare_assignment_draft | W3 | Mgr | Draft | Pending |
| 12 | prepare_waiver_request | W3 | Mgr,Owner | Draft | Pending |
| 13 | prepare_validation_decision | W3 | Val | Draft | Pending |

---

## Week 1: Read-Only Tools (3/13)

All Week 1 tools are **read-only** with no database modifications. Authorization enforced by backend.

### Tool 1: search_certifications

**Purpose:** Find certifications by keyword, vendor, market signals

**Input:**
```json
{
  "query": "string (required)",
  "filters": {
    "provider": ["AWS", "GCP", "Azure"],
    "market_demand": ["high", "moderate", "low"],
    "is_trending": boolean,
    "difficulty_level": ["beginner", "intermediate", "advanced"]
  },
  "limit": 20
}
```

**Output:**
```json
{
  "results": [
    {
      "cert_id": "uuid",
      "certification_name": "string",
      "provider": "string",
      "market_demand": "high|moderate|low",
      "is_trending": boolean,
      "validity_months": 36
    }
  ],
  "total_found": number
}
```

**Authorization:** All roles  
**Safety:** No PII, results limited to 50  

---

### Tool 2: list_team_certs

**Purpose:** Show team certification status for manager

**Input:**
```json
{
  "unit_id": "uuid",
  "status_filter": ["active", "expired", "pending"]
}
```

**Output:**
```json
{
  "unit_name": "string",
  "certifications": [
    {
      "collaborator_id": "uuid",
      "collaborator_name": "John D. (masked)",
      "certification_name": "string",
      "status": "active|expired|pending_validation",
      "expiration_date": "YYYY-MM-DD",
      "days_until_expiration": number
    }
  ],
  "coverage_pct": number
}
```

**Authorization:** Manager (own unit only), Auditor (all)  
**Safety:** PII masked, RBAC enforced  

---

### Tool 3: check_compliance_gap

**Purpose:** Identify missing required certifications by role/unit

**Input:**
```json
{
  "unit_id": "uuid (optional)",
  "role_id": "uuid (optional)"
}
```

**Output:**
```json
{
  "gaps": [
    {
      "collaborator_id": "uuid",
      "required_cert": "string",
      "status": "missing|in_progress",
      "recommended_action": "assign|waiver|monitor"
    }
  ],
  "summary": {
    "total_gaps": number,
    "coverage_pct": number
  }
}
```

**Authorization:** Manager, Owner, Auditor  
**Safety:** Read-only, RBAC enforced  

---

## Week 2: Advanced Read-Only Tools (7/13)

Tools 4-10 perform complex queries but return read-only data.

### Tool 4-10 Summary

- Tool 4: get_assignment_info — fetch assignment status
- Tool 5: suggest_renewal_candidates — identify near-expiration certs
- Tool 6: explain_validation_rules — show validator requirements
- Tool 7: list_available_waivers — check waiver status
- Tool 8: get_certification_timeline — show cert history
- Tool 9: estimate_coverage_impact — simulate action impact
- Tool 10: suggest_equivalent_certs — find cert alternatives

---

## Week 3: Draft-Confirmation Tools (3/13)

Tools 11-13 create drafts without DB changes. Require explicit confirmation.

### Tool 11: prepare_assignment_draft

**Purpose:** Draft assignment for manager approval

**Input:**
```json
{
  "collaborator_id": "uuid",
  "certification_id": "uuid",
  "due_date": "YYYY-MM-DD",
  "priority": "low|medium|high"
}
```

**Output:**
```json
{
  "draft_id": "uuid",
  "status": "pending_human_review",
  "preview": {
    "collaborator": "John D.",
    "certification": "AWS SAA",
    "due_date": "2026-12-31"
  },
  "confirmation_url": "https://app.../confirm/draft/{draft_id}"
}
```

**Next Step:** Manager clicks "Confirm" button (no direct tool API call)  
**Authorization:** Manager  
**Safety:** No DB write, confirmation required  

---

### Tool 12: prepare_waiver_request

Similar to Tool 11 but for waivers (Manager/Owner)

---

### Tool 13: prepare_validation_decision

Similar to Tool 11 but for validator decisions (Validator only)

---

## Safety Constraints (All Tools)

1. **PII Minimization:** Names masked, no email/phone
2. **Prompt Injection:** Input sanitized, parameterized queries
3. **Authorization:** RBAC enforced per role
4. **Rate Limiting:** Max 1000 invocations/hour
5. **Confirmation:** Write operations require explicit human confirm

---

**Detailed specifications:** See docs/06-agent-ai/herramientas.md  
**Test plan:** See docs/06-agent-ai/EVALUATION-PLAN.md (not yet created)  
**Status:** W1 implementation in progress
