# MCP Tool Contract

## Protocol

- Transport: stdio (JSON-RPC 2.0)
- Specification: [Model Context Protocol](https://modelcontextprotocol.io)
- Server starts on stdio and communicates via line-delimited JSON-RPC messages

## Server Capabilities

On MCP `initialize` handshake, the server advertises:

```json
{
  "protocolVersion": "2025-03-26",
  "capabilities": {
    "tools": {
      "listChanged": false
    }
  },
  "serverInfo": {
    "name": "specmetrics",
    "version": "0.1.0"
  }
}
```

---

## Tool: `measure`

Execute the measurement pipeline.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_path` | `string` | Yes | Absolute or relative path to project |
| `output_format` | `string` | No | Export format: `json`, `csv`, `xml` (default: `json`) |
| `from_stage` | `string` | No | Start from stage: `discover`, `extract`, `graph`, `cfm`, `rule`, `measure`, `export` |

### Response

```json
{
  "content": [
    {
      "type": "text",
      "text": "{ serialized PipelineResult as JSON }"
    }
  ],
  "isError": false
}
```

### Error Response

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"status\": \"failed\", \"error\": \"Project path not found: /invalid/path\"}"
    }
  ],
  "isError": true
}
```

### Example

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "measure",
    "arguments": {
      "project_path": "/home/user/my-project",
      "output_format": "json"
    }
  }
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"status\":\"success\",\"total_function_points\":145,\"duration_seconds\":12.4}"
      }
    ]
  }
}
```

---

## Tool: `plugins_list`

List installed plugins.

### Parameters

None.

### Response

```json
{
  "content": [
    {
      "type": "text",
      "text": "[{\"name\":\"fpa\",\"version\":\"0.1.0\",\"type\":\"measurement\",\"enabled\":true,\"compatible\":true}]"
    }
  ]
}
```

---

## Tool: `specmetrics_version`

Get platform and plugin version information.

### Parameters

None.

### Response

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"platform_version\":\"0.1.0\",\"python_version\":\"3.13.3\",\"plugins\":[]}"
    }
  ]
}
```

---

## JSON-RPC Error Codes

| Code | Meaning | When |
|------|---------|------|
| `-32700` | Parse error | Invalid JSON in request |
| `-32600` | Invalid request | Malformed JSON-RPC structure |
| `-32601` | Method not found | Unknown tool name |
| `-32602` | Invalid params | Missing or invalid tool arguments |
| `-32603` | Internal error | Pipeline execution failure |
| `-32000` | Pipeline error | Measurement-specific error (project not found, no specs) |
