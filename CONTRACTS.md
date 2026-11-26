# Adaptive UI Service contracts

## Intent normalization

`normalize_intent(raw_text, user_context)` accepts non-empty natural-language text and
a JSON-serializable context dictionary. `user_context.capabilities` is a list of
capability IDs or objects with an `id` field. `user_context.destinations` is a list of
destination IDs or objects with an `id` field. The model may only refer to IDs in
these lists.

The asynchronous function returns an object matching
[`adaptive_ui_service/schemas/intent.json`](adaptive_ui_service/schemas/intent.json):

```json
{
  "action": "move",
  "target_capability_id": "time_charts",
  "destination": "secondary_panel",
  "confidence": 0.95,
  "clarification_question": null
}
```

`action` is one of `move`, `hide`, `show`, `reorder`, `unsupported`, or `clarify`.
`confidence` is between 0 and 1. `target_capability_id`, `destination`, and
`clarification_question` may be `null`; non-null capability and destination values
must be present in `user_context`.

Invalid input raises `IntentValidationError`. Missing Gemini configuration, provider
failures, absent function calls, malformed arguments, schema violations, or references
outside the supplied context raise `NormalizationError`. The API key is read from
`GEMINI_API_KEY`; model, base URL, and timeout are configurable with `GEMINI_MODEL`,
`GEMINI_BASE_URL`, and `GEMINI_TIMEOUT`.
