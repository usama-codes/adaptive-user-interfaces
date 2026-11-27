# Adaptive UI Service Contracts

## Capability Manifest Entry

**File:** `data/capability_manifest.json`

| Field | Type | Required | Description |
|---|---|---|---|
| `capability_id` | `string` | Yes | Unique snake_case identifier |
| `name` | `string` | Yes | Short display name |
| `description` | `string` | Yes | Natural-language description used for embedding in T2.4 |
| `category` | `string` | Yes | One of `time_charts`, `view_toggles`, `column_visibility`, or `widget_placement` |
| `required_permissions` | `list[string]` | Yes | OpenProject permission names returned by `/api/v3/roles/:id`; an empty list means visible to all project members |
| `ui_change` | `object` | Yes | Opaque diff payload applied by the widget; the schema is defined in `schemas/diff.json` in T3.1 |
