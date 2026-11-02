# {{API_TITLE}} — API Documentation

> Reverse engineered from `{{TARGET_URL}}`
> Generated on: `{{TIMESTAMP}}`

---

## Base URL

```
{{BASE_URL}}
```

## Authentication

| Method | Location | Details |
|--------|----------|---------|
| {{AUTH_TYPE}} | {{AUTH_LOCATION}} | {{AUTH_DETAILS}} |

### Auth Setup

```bash
# Environment variable
export API_TOKEN="your_token_here"
```

```python
# Python
headers = {"Authorization": f"Bearer {os.environ['API_TOKEN']}"}
```

```javascript
// JavaScript
const headers = { 'Authorization': `Bearer ${process.env.API_TOKEN}` };
```

---

## Endpoints

### {{RESOURCE_NAME}}

#### `{{METHOD}} {{PATH}}`

{{DESCRIPTION}}

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| {{PARAM_NAME}} | {{PARAM_IN}} | {{PARAM_TYPE}} | {{PARAM_REQUIRED}} | {{PARAM_DESC}} |

**Request Body:**

```json
{{REQUEST_BODY_EXAMPLE}}
```

**Response:** `{{STATUS_CODE}}`

```json
{{RESPONSE_BODY_EXAMPLE}}
```

**Code Examples:**

<details>
<summary>cURL</summary>

```bash
curl -X {{METHOD}} "{{BASE_URL}}{{PATH}}" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{{REQUEST_BODY_EXAMPLE}}'
```

</details>

<details>
<summary>Python</summary>

```python
import requests

response = requests.{{METHOD_LOWER}}(
    "{{BASE_URL}}{{PATH}}",
    headers={"Authorization": f"Bearer {token}"},
    json={{REQUEST_BODY_PYTHON}}
)
data = response.json()
```

</details>

<details>
<summary>JavaScript</summary>

```javascript
const response = await fetch("{{BASE_URL}}{{PATH}}", {
  method: "{{METHOD}}",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({{REQUEST_BODY_JS}}),
});
const data = await response.json();
```

</details>

---

## Error Responses

| Status | Meaning | Description |
|--------|---------|-------------|
| 400 | Bad Request | Invalid request body or parameters |
| 401 | Unauthorized | Missing or invalid auth token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 422 | Unprocessable | Validation error |
| 429 | Rate Limited | Too many requests |
| 500 | Server Error | Internal server error |

## Rate Limiting

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Max requests per window |
| `X-RateLimit-Remaining` | Remaining requests |
| `X-RateLimit-Reset` | Window reset timestamp |

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- Pagination uses `?page=` and `?per_page=` query parameters
- IDs are {{ID_FORMAT}} format
- All request/response bodies are JSON (`Content-Type: application/json`)
