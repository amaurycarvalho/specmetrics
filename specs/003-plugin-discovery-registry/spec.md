# Feature Specification: Plugin Discovery & Registry

**Feature Branch**: `003-plugin-discovery-registry`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "F02 — Plugin Discovery & Registry"

---

## User Scenarios & Testing

### User Story 1 — Automatic plugin discovery at startup (Priority: P1)

A developer installs a SpecMetrics plugin via pip and the system automatically
discovers it on next startup — no manual registration required.

**Why this priority**: Without plugin discovery, no extension point can function.
This is the gateway for every adapter, semantic provider, measurement engine,
exporter, and publisher.

**Independent Test**: Can be tested by installing a mock plugin package that
declares a SpecMetrics entry point, starting the system, and verifying the
plugin appears in the registry.

**Acceptance Scenarios**:

1. **Given** a Python package declaring a `specmetrics.plugins` entry point,
   **When** the system starts, **Then** the plugin is automatically discovered
   and registered
2. **Given** multiple installed plugins, **When** the system starts, **Then**
   all plugins are discovered and available in the registry
3. **Given** a plugin is installed after system startup, **When** the system is
   restarted, **Then** the new plugin is discovered
4. **Given** no SpecMetrics plugins are installed, **When** the system starts,
   **Then** the registry is empty and no error is raised

---

### User Story 2 — Plugin compatibility validation (Priority: P1)

A developer installs a plugin built for an incompatible API version and the
system reports the incompatibility clearly, preventing runtime failures.

**Why this priority**: Silent plugin incompatibility would cause unpredictable
pipeline failures. Early validation protects measurement integrity.

**Independent Test**: Can be tested by installing a plugin declaring an
incompatible API version and verifying the system reports the incompatibility.

**Acceptance Scenarios**:

1. **Given** an incompatible plugin, **When** the system starts, **Then** the
   plugin is NOT registered and a clear error message describes the version
   mismatch
2. **Given** a compatible plugin, **When** the system starts, **Then** the
   plugin is registered successfully without warnings
3. **Given** a plugin with missing required interfaces, **When** validation
   runs, **Then** the plugin is rejected and the missing interfaces are listed

---

### User Story 3 — Registry lookup for pipeline orchestration (Priority: P1)

The Pipeline Engine queries the registry to find handlers for each event type
and the registry returns all matching plugins.

**Why this priority**: The kernel Pipeline Engine (F01) depends on the registry
to resolve event handlers at runtime.

**Independent Test**: Can be tested by registering mock plugins, then querying
the registry by event type and verifying the correct handlers are returned.

**Acceptance Scenarios**:

1. **Given** a populated plugin registry, **When** the Pipeline Engine queries
   for a specific event type, **Then** the correct handler plugin is returned
2. **Given** no plugin handles a given event type, **When** queried, **Then**
   the registry returns empty (no handler)
3. **Given** multiple plugins handling the same event type, **When** queried,
   **Then** the registry returns all matching plugins in registration order

---

### User Story 4 — Graceful plugin loading errors (Priority: P2)

A developer installs a corrupted or malformed plugin and the system continues
to operate with the remaining plugins, reporting the specific error for the
faulty one.

**Why this priority**: A single broken plugin should not block the entire
platform. Graceful degradation improves reliability.

**Independent Test**: Can be tested by placing a malformed plugin in the
discovery path and verifying the system starts with remaining plugins intact.

**Acceptance Scenarios**:

1. **Given** a plugin that raises an error during loading, **When** the system
   starts, **Then** the faulty plugin is skipped and the error is logged with
   its identifier
2. **Given** one faulty and one healthy plugin, **When** the system starts,
   **Then** the healthy plugin is registered normally while the faulty one is
   skipped
3. **Given** a plugin with dependencies on other plugins, **When** a dependency
   is missing, **Then** the dependent plugin is skipped and the missing
   dependency is reported

---

### Edge Cases

- What happens when two plugins declare the same entry point name? The last one
  discovered wins and a warning is logged.
- What happens when a plugin's dependencies are not installed? The plugin is
  skipped and missing dependencies are reported.
- What happens when a plugin is dynamically loaded and immediately raises an
  exception? The loading error is caught, logged, and the plugin is not
  registered; the system continues.
- How does the system handle namespace packages versus regular packages for
  entry points? Standard Python entry point resolution is used — no special
  handling needed.
- What happens when a plugin declares an API version string that cannot be
  parsed? The plugin is rejected with a clear error about the unparseable
  version.

---

## Constitution Check

**Engaged Principles**:

- VIII (Plugin-Oriented) — Plugin discovery and registry is the core mechanism
  enabling the plugin-oriented architecture. All extension points are
  discovered through this unified mechanism.
- XII (Open by Default) — Python Entry Points are an open, documented standard.
  Any Python package can declare SpecMetrics plugins without proprietary
  tooling.
- XIII (Evolution Without Disruption) — API version validation ensures
  plugins built for different API versions do not disrupt the platform or each
  other.

**Compliance Notes**: The registry is a discovery and validation layer only. It
does not execute plugin logic, mutate plugin state, or bypass the Kernel's
event-driven orchestration. Plugin isolation is preserved because the registry
simply returns handler references — it never calls plugins directly.

---

## Requirements

### Functional Requirements

- **FR-001**: The Plugin Registry MUST discover plugins via Python Entry Points
  under the `specmetrics.plugins` group at startup
- **FR-002**: Each discovered plugin MUST declare its API version, plugin type
  (adapter, semantic, measurement, exporter, publisher), and handled event
  types via entry point attributes
- **FR-003**: The Plugin Registry MUST validate API version compatibility
  between each plugin and the running platform before registering it
- **FR-004**: The Plugin Registry MUST reject plugins with missing required
  interfaces and report which interfaces are absent
- **FR-005**: Plugin loading errors (import failures, invalid metadata) MUST
  NOT prevent other plugins from loading — faulty plugins are skipped
- **FR-006**: The Plugin Registry MUST provide a lookup method that returns
  all handlers registered for a given event type
- **FR-007**: The Plugin Registry MUST expose the set of all registered plugin
  identifiers for lifecycle inspection
- **FR-008**: The Plugin Registry MAY support multiple handlers for the same
  event type, returned in registration order
- **FR-009**: The Plugin Registry MUST log a warning when duplicate entry point
  names are detected and use the last discovered registration
- **FR-010**: The Plugin Registry MUST NOT execute any plugin business logic
  during discovery or registration

### Key Entities

- **Plugin Metadata**: Declared information about a plugin — identifier, API
  version, plugin type, author, description, and list of handled event types
- **Plugin Descriptor**: Internal representation of a discovered plugin,
  containing its metadata, entry point reference, and validation status
- **Plugin Registry**: Central store mapping plugin types and event types to
  discovered, validated plugin instances
- **API Version**: Semantic version string that defines the Plugin API contract
  between the platform and plugins (e.g., `1.0.0`)

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: A mock plugin package declaring a valid entry point is
  automatically registered on system startup without manual configuration
- **SC-002**: An incompatible plugin is rejected with a specific error message
  identifying the version mismatch within 2 seconds of startup
- **SC-003**: A corrupted plugin does not prevent other plugins from loading;
  at least one healthy plugin remains registered in the presence of one faulty
  plugin
- **SC-004**: The Pipeline Engine can retrieve a registered handler for any
  event type within 100ms of querying the registry
- **SC-005**: The registry correctly handles 50+ simultaneously installed
  plugins without performance degradation or startup delay exceeding 5 seconds

---

## Assumptions

- Plugins are standard Python packages installed via pip; no custom package
  manager is needed
- Entry point groups follow the convention `specmetrics.plugins.{type}` (e.g.,
  `specmetrics.plugins.adapters`)
- API versioning follows Semantic Versioning (SemVer) 2.0.0 — major version
  mismatches are rejected, minor/patch bumps within the same major version are
  accepted
- Plugin discovery runs once at startup; runtime discovery of new plugins
  requires a restart
- The registry is consumed by the Kernel (F01) and Application Layer (F08) but
  owned by neither — it is an independent component
- Plugin validation is syntactic (interface compliance, version matching) not
  semantic (correctness of plugin logic)
