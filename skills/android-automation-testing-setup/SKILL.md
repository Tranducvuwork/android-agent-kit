---
name: android-automation-testing-setup
description: Analyze and create a testing strategy for Android apps that use XML layouts and Views. Set up unit, Espresso UI, screenshot, and end-to-end tests.
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-29'
  keywords:
  - android
  - xml
  - views
  - espresso
  - testing
  - screenshot tests
  - coverage
---

## Mandatory project extension: coverage and production protection

These requirements take precedence over the preserved twelve-step guide below.
Use this skill across Android XML/Views projects; discover project-specific
packages and workflows instead of assuming an app, module, variant or DI stack.

- Write and run automation tests; never fix application bugs or change production
  code, resources, manifests, DI, interfaces, business behavior or release settings.
  This overrides the test-seam/DI changes suggested in Steps 2 and 4. Allow only
  test source sets, test helpers/fixtures, reports and minimal test-only dependency
  or runner configuration. Keep existing user changes intact. If testing requires
  a production change, retain the case as blocked and explain the prerequisite.
- Read [coverage-workflow.md](references/coverage-workflow.md) and
  [automation-reporting-workflow.md](references/automation-reporting-workflow.md)
  before planning. Default TEST covers all applicable workflows of the selected
  app/variant, including contributing modules. Explicit focused or analysis-only
  requests retain their scope. Unsupported UI remains an explicit coverage gap.
- Inventory packages, workflows and behavioral branches before selecting cases.
  Mirror production packages for component tests; separate multi-screen and long
  journeys under test-only workflows packages. Every case has one primary owner.
- Use [coverage-format.md](references/coverage-format.md) for the versioned
  coverage v2 artifact, runner collector and design/implementation/execution gates.
  Execution reparses current runner evidence and checks production live.
  Do not claim full-app coverage from a small passing suite or a case count alone.
- Read [failure-evidence.md](references/failure-evidence.md) when adding UI tests.
  Capture reproducible UI failures before cleanup where possible, preserve all
  attempts and the original exception, and explain unavailable screenshots.
- Save PROJECT_ROOT/autotesting-reports/<run-id>/report.md and grouped reports.
  PASS/FAIL require current runner evidence. RETEST preserves all baseline IDs,
  expected results and history; expanded coverage needs a new TEST baseline.

The original twelve steps and references are preserved as framework guidance.

## Step 1: Analyze the current testing setup

Inspect the project before changing dependencies or build configuration. Read the
version catalog and module build files, and identify:

1. UI implementation: XML layouts and Views, Compose, or a hybrid. This skill
   covers XML layouts and Views. For hybrid apps, analyze and test only the
   Views portion; do not apply these instructions to Compose screens. If the
   project has no Views UI, report that it is outside this skill's scope.
2. Dependency injection framework, if any, such as Koin, Hilt, Dagger, or
   another existing framework.
3. Local and instrumented test frameworks, JUnit version, mocking framework,
   Robolectric usage, and configured instrumentation runner.
4. View testing libraries, such as Espresso, AndroidX Test, or an existing
   wrapper such as Kaspresso.
5. Screenshot testing tools and whether they run on the host, with Robolectric,
   or on a device.
6. Database and navigation frameworks that need dedicated testing.
7. Existing test, screenshot, and coverage tasks for each relevant module.

Generate a Markdown report of the findings when the user asks for analysis or
testing setup work.

## Step 2: Dependency injection for tests

Respect the dependency injection framework already used by the project. Do not
replace it solely to add tests. When the project uses Koin, consult the
[Koin unit testing guide](https://insert-koin.io/docs/reference/koin-test/testing/)
and [Koin Android instrumented testing guide](https://insert-koin.io/docs/reference/koin-android/instrumented-testing/).
Use the project's existing Koin version or BOM when adding Koin test artifacts.

For Koin tests:

- Use test modules to replace network, database, or other slow dependencies
  with fakes. Load test overrides after production definitions when the test
  setup uses both.
- Match the Koin test artifact to the project's JUnit version (for example,
  `koin-test-junit4` or `koin-test-junit5` for JVM tests); use the Android test
  artifact required by the configured instrumented test runner.
- Use a per-test Koin rule/container where possible to isolate global state.
  If the project uses a shared test `Application`, reset singleton fakes
  between tests.
- Configure Koin before launching an Activity or Fragment. Ensure the Koin
  rule runs before any rule that launches the UI.
- Put Android instrumented dependencies and test configuration in
  `androidTest`; keep JVM-only Koin tests in `test`.

For other existing DI frameworks, follow that framework's official testing
documentation and preserve its established test setup. If no DI framework is
present, do not add one just for testability. If the user requests DI setup,
prefer Koin unless they specify another framework, and explain the app-level
change before making it.

## Step 3: Select test frameworks

Unless the user specifies otherwise, preserve the project's current test stack.
If a required test layer is missing, add only the dependencies needed for the
requested testing work and align versions with the project's version catalog,
platform, and existing test framework.

- Use the existing local unit test framework for business logic.
- Use Espresso for XML View behavior tests. Instrumented Espresso tests belong
  in `androidTest` and run with the configured Android test runner on a device
  or emulator.
- Use Robolectric for local tests that need Android framework behavior only
  when the project already uses it or the user requests host-side execution.
  Do not assume Espresso UI tests belong in `test` or are runnable with
  Robolectric.
- Use UI Automator when a test must interact with system UI or cross app
  boundaries.
- Add a mocking library only when fakes are impractical and the project does
  not already have a suitable one.
- Add or configure coverage tooling only when requested or when it is already
  part of the project's quality workflow. Do not add JaCoCo to every module
  automatically.

## Step 4: Create fakes and test seams

For unit tests, prefer fakes for dependencies that can be replaced cleanly. If
production code depends directly on an external or Android framework class,
introduce an interface and a default implementation only when the seam is
useful beyond the test. Otherwise, use the mocking framework already present
when necessary.

For UI tests, use runtime fakes through the project's existing DI framework to
cover scenarios such as invalid credentials, server errors, missing
permissions, or unavailable platform features. Fakes can also replace network
or persistent storage with deterministic in-memory implementations.

## Step 5: Unit tests

Add or review unit tests for business logic such as ViewModels, repositories,
use cases, and database logic. Test Activities and Fragments through UI or
component tests rather than treating their rendered Views as plain unit-test
logic. Do not add tests solely for dependency injection configuration unless
they verify an important graph or module contract.

## Step 6: XML View behavior tests

Write Espresso behavior tests in the module's `src/androidTest` source set.
Configure `testInstrumentationRunner` only when it is missing or the selected
DI/testing framework requires a custom runner. Follow the project's existing
runner and rules conventions.

- Locate XML Views primarily by stable resource IDs, and assert user-visible
  outcomes after actions.
- Cover loading, success, empty, and error states where applicable, plus
  validation and accessibility-relevant behavior.
- Use Espresso idling resources or the project's established synchronization
  mechanism for asynchronous work; avoid arbitrary sleeps.
- Test Activity or Fragment recreation and state restoration when the screen is
  expected to preserve user state.
- For Koin-backed screens, configure test definitions before launching the
  Activity or Fragment.

Use local Robolectric tests only for cases where the project supports them and
they provide a useful faster test layer; keep device-dependent behavior in
`androidTest`.

## Step 7: Database tests

When using SQLite through Room, SQLDelight, or a similar library, include tests
that exercise the SQLite implementation with an in-memory database. Use
instrumented tests when the behavior depends on the device SQLite engine; use
an existing supported local test setup when it provides equivalent coverage.

## Step 8: XML screenshot tests

Keep the screenshot framework already configured in the project. Do not
combine or migrate screenshot frameworks as part of unrelated testing work. If
the project has no screenshot framework and screenshot tests are requested,
evaluate Paparazzi for host-side View rendering against the project's AGP,
Gradle, JDK, resources, and custom View requirements before adding it. If it
isn't compatible, report the constraint and recommend a device-based option
rather than silently changing the build stack.

Use screenshots to detect visual regressions, not to verify behavior. Choose a
representative set of screen sizes supported by the app, including compact and
expanded layouts when applicable. Add relevant variations for themes/night
mode, larger font scale, locale, and important loading, empty, or error states.
Cover reusable Views/components where visual regressions would affect several
screens. Avoid requiring every screen to have a fixed nine-size matrix unless
the project specifically requires it.

Use Dropshots or the existing device screenshot framework when verifying
rendering that depends on a real device, system UI, edge-to-edge behavior,
notifications, or picture-in-picture.

## Step 9: Navigation tests

Use UI behavior tests to verify navigation paths that matter to the app,
including back handling, deep links, and multiple back stacks if the app uses
them. Test both the destination and the user-visible result of navigation.

## Step 10: Window sizes and system settings

For Views, use the selected screenshot tool's device/configuration settings or
an emulator/device configuration to exercise supported screen sizes, density,
font scale, locale, and night mode. Do not use Compose-only configuration APIs
for XML layouts.

## Step 11: End-to-end tests

Keep end-to-end coverage focused on a small number of high-value user journeys.
Use Espresso for flows contained within the app and UI Automator when the flow
crosses into system UI or another app. Run these tests on a device or emulator.

## Step 12: Screenshot tests on a device

When device-based screenshots are requested or needed to verify platform
rendering, keep the project's current screenshot tool. If none exists, evaluate
Dropshots and configure its plugin and JUnit rule using its current
documentation. Store and update reference images only through the established
workflow for that tool.

## Final touches

When the user asks to document the analysis or testing strategy, update the
project's existing testing documentation. If there is no suitable document,
create `docs/testing.md` with the test layers, commands, source set locations,
and screenshot reference locations. Do not create or modify an `AGENTS.md`
unless the user requests repository guidance changes.
