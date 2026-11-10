# Coverage artifact v2 và CLI

Python 3.9+ (standard library) cần cho collector, validator và guard; chạy từ bất kỳ working directory.
`SKILL_DIR` là gói đang cài, `PROJECT_ROOT` là app đang kiểm thử, `RUN_DIR` là thư mục
run. Resolve các đường dẫn trước khi chạy. Collector chạy lệnh test được cung cấp;
validator/guard chỉ đọc, không sửa app hoặc tự chạy lại test.

## Artifact

Khởi tạo `RUN_DIR/test-evidence/inputs/coverage.json` từ
[template](../assets/templates/coverage-template.json). Template chưa hoàn chỉnh,
không chứa kết quả app thật. Thay dữ liệu ví dụ, không chỉ bật discovery_complete.

- `version`: số 2 cho run mới.
- `project`: root tuyệt đối, application_id, module, variant, source_ref, branch,
  skill_ref. Dùng nguồn thực tế; ref không có Git là hash snapshot, branch ghi `no-git`.
- `run`: id (khớp tên thư mục run), mode TEST/RETEST, started_at ISO-8601 có timezone;
  ended_at là null khi đang chạy, bắt buộc có thời gian hợp lệ trước execution gate.
- `executions`: [{id, manifest, sha256}]. Collector trả các giá trị này; manifest
  tính tương đối từ RUN_DIR. Không sửa manifest hoặc raw evidence sau khi thu.
- `baseline`: chỉ RETEST v2, {run_dir, sha256}; run_dir tương đối từ RUN_DIR tới
  baseline TEST gốc, sha256 của artifact coverage baseline đã đọc. Được dùng `..`
  ở liên kết baseline; evidence và screenshot không được phép traversal.
- `scope`: kind full_app/focused, description, discovery_complete, discovery_sources
  đã kiểm tra; exclusions chứa source_ref/reason. Cấu hình môi trường/giới hạn tích
  hợp được mô tả thêm trong report, không dùng exclusions để bỏ việc chưa làm.
- `packages`: id là full package name, source_refs, disposition covered,
  not_applicable, out_of_scope (chỉ focused) hoặc gap; ba loại cuối cần reason.
- `workflows`: id WF-001..., name, kind screen/multi_screen/cross_package/long,
  source_refs, related_packages, screens (có thể rỗng cho nghiệp vụ không UI).
  Feature bất hoạt ở variant nằm trong exclusions, không dựng workflow rỗng.
- `obligations`: id ổn định, package_id, workflow_id, description, expected,
  applicable boolean, case_ids. Không áp dụng cần reason và case_ids rỗng.
  Applicable thiếu expected/case_ids vẫn giữ trong draft, khiến design gate chưa đạt.
- `cases`: id AT-001..., name, module/variant thực sự chạy case (có thể khác module
  app ở metadata), owner {kind: package/workflow, id}, related_packages,
  workflow_ids, screens, layer (unit/database/ui/navigation/e2e/screenshot),
  preconditions, steps (array), expected, checkpoints [{id, action, expected}].
  Workflow owner cần ít nhất hai checkpoint hành vi. Mỗi case ánh xạ ít nhất một
  applicable obligation. Workflow nhiều màn/cross-package/dài cần journey case
  riêng, không chỉ tập hợp unit cases.
- `automation`: trong mỗi case, implemented boolean, symbol hiện thực thi,
  source test file tương đối từ PROJECT_ROOT. File đã triển khai phải tồn tại
  trong source set test; component mirror package owner, journey ở package workflows.
  Chưa viết dùng false và chuỗi rỗng, ghi lý do ở result. Project dùng custom test
  source roots cần thích nghi quy tắc validator rõ ràng, không trỏ source production.
- `result`: status PASS/FAIL/BLOCKED/NOT_TESTED, reason khi chưa hoàn tất, attempts.
- Mỗi attempt: id, run_id, source_ref, module, variant, symbol, status PASS/FAIL, actual,
  started_at/ended_at ISO-8601 có timezone, evidence (array đường dẫn tương đối
  **từ RUN_DIR**). Chỉ case đã runner thực thi mới có completed attempt; lỗi build
  được dẫn ở report với BLOCKED, không dựng attempt FAIL cho mọi case.
- Attempt v2 có `runner_result`: {execution_id, class_name, test_name, ordinal}.
  class_name và test_name giữ nguyên từ raw runner, kể cả parameter; symbol phải
  bằng `class_name + "." + test_name`. Ordinal bắt đầu từ 1 cho cùng class/name
  trong một execution, kể cả retries và skip. Thời gian attempt nằm trong execution;
  nếu runner không cho timestamp từng case, dùng khoảng invocation và ghi rõ độ phân giải.
- Attempt FAIL có screenshot {status: captured/unavailable/not_applicable, reason,
  files}. UI/navigation/E2E/screenshot failure cần captured hoặc unavailable có lý
  do; unit không có UI dùng not_applicable. Mỗi file có path PNG, checkpoint_id,
  timing failure/before_crash/after_crash và captured_at. Path phải thuộc đúng
  `test-evidence/screenshots/<case-id>/<attempt-id>/`. Không chia sẻ ảnh giữa case.
  Từ chối absolute path, `..`, symlink; chống dùng lại cùng inode/hardlink. Ảnh khác
  file nhưng giống nội dung vẫn hợp lệ. PNG vẫn chỉ kiểm tra header, không giải mã.
- `production_guard`: before/after là đường dẫn snapshot JSON từ RUN_DIR, unchanged
  boolean. `test_config_changes`: [{path, reason, test_only_reviewed: true}].
  Diff review test-only là trách nhiệm agent; guard không suy diễn Gradle semantics.
- `summary` tùy chọn, nếu có phải khớp output validator: cases, obligations,
  implemented, executed và statuses cho đủ bốn status. Không đưa số mẫu vào report.

Artifact mỗi run lưu kết quả của run đó. Nếu có FAIL rồi retry PASS trong cùng run,
status case vẫn FAIL; ghi hành vi không ổn định và đủ attempts. RETEST sau là run mới.

## Collector và raw runner evidence

Tạo artifact v2 và snapshot production trước khi viết test. Collector không tự
thêm case/attempt hoặc thay expected. Chạy command dạng argv, không shell mặc định.
Ví dụ JVM (thay task/pattern bằng discovery thực tế):

```sh
python3 "$SKILL_DIR/scripts/record-test-run.py" "$RUN_DIR" \
  --execution-id unit-1 --module app --variant debug --format junit-xml \
  --results 'app/build/test-results/testDebugUnitTest/*.xml' \
  -- ./gradlew :app:testDebugUnitTest --rerun-tasks --no-build-cache
```

`--results` lặp được, tính từ PROJECT_ROOT; XML phải là file mới/được ghi lại trong
invocation theo fingerprint trước/sau (device/inode/size/mtime/ctime/SHA-256).
File cũ không đổi không được thu. Command Gradle phải có hai flag trên; không coi
cache/up-to-date là thực thi. Không tự chọn task hoặc xóa output cũ của người dùng.

Instrumentation dùng raw protocol từ stdout, luôn chọn serial cụ thể:

```sh
python3 "$SKILL_DIR/scripts/record-test-run.py" "$RUN_DIR" \
  --execution-id ui-1 --module app --variant debug --format instrumentation \
  -- "$ADB" -s "$SERIAL" shell am instrument -w -r "$TEST_APPLICATION_ID/$RUNNER"
```

Discovery và build/install APK test trước lệnh instrumentation; không tự chọn
thiết bị giữa nhiều máy. Có thể dùng `--timeout SECONDS` cho cả hai định dạng.
stdout CLI collector là JSON gồm execution_id, manifest, sha256, exit_code và
collector_errors. Thêm reference vào executions và mapping từng attempt, không
chép normalized results làm bằng chứng thay raw.

Mỗi execution ở `test-evidence/checks/executions/<execution-id>/`: manifest.json,
stdout.txt, stderr.txt, và bản sao XML mới nếu có. ID không ghi đè. Manifest v1 nội bộ
(khác coverage v2) chứa id/run_id/source_ref/project_root/module/variant/format,
command argv, working_directory, serial, started_at/ended_at, exit_code,
collector_errors, files [{path, role, sha256, original/before/after khi là XML}],
và results normalized chỉ để hỗ trợ mapping. Role gồm stdout/stderr/result.
Validator kiểm hash manifest/raw và tự parse lại raw, không tin trường results.
Mọi thư mục execution của run phải được đăng ký trong catalog; không bỏ reference
của invocation cũ để che retry/FAIL. Case chạy ngoài inventory không được cộng vào tổng.
Log stdout/stderr có thể rỗng; evidence mà attempt dẫn tới phải không rỗng (ví dụ manifest).

JUnit XML yêu cầu testsuite/testsuites và testcase có classname/name. Failure/error
là FAIL; skipped không phải PASS. flakyFailure/rerunFailure (và biến thể Error)
được giữ như các attempt FAIL. Instrumentation ghép start(1) với terminal pass(0),
error(-1), fail(-2); ignored(-3)/assumption(-4) là skipped. Case thiếu terminal hoặc
process crash chưa có kết luận riêng là BLOCKED. Mỗi kết quả chỉ gắn một attempt;
không bỏ các completed retries của testcase trong executions đã đăng ký.

Exit code command khác 0 không biến mọi case thành FAIL: giữ terminal results đã có,
case chưa kết luận dùng BLOCKED. Skip có blocker dùng BLOCKED, còn lại NOT_TESTED;
hai loại này không tạo completed attempt. Collector trả exit code command khi thu
thành công; lỗi collector/start/timeout trả 2 và giữ exit_code thực tế riêng trong
manifest. Collector không tự retry, không tự chạy giao dịch ngoài phạm vi được phép.
Hash phát hiện file thay đổi sau capture, không chứng thực chống giả mạo.

Ví dụ mapping sau khi collector trả reference (thay ID/hash/time bằng dữ liệu thật):

```json
{
  "executions": [{
    "id": "unit-1",
    "manifest": "test-evidence/checks/executions/unit-1/manifest.json",
    "sha256": "<collector-manifest-sha256>"
  }],
  "runner_result": {
    "execution_id": "unit-1",
    "class_name": "com.example.LoginTest",
    "test_name": "invalidPassword[empty]",
    "ordinal": 1
  }
}
```

`executions` nằm ở root artifact; `runner_result` nằm trong mỗi completed attempt,
không phải field root. Ví dụ symbol tương ứng là
`com.example.LoginTest.invalidPassword[empty]`. Khi RETEST thêm ở root:

```json
{"baseline": {"run_dir": "../<run-id-test>", "sha256": "<baseline-coverage-json-sha256>"}}
```

## Production guard

Trước khi sửa test/cấu hình, chạy script và lưu stdout JSON vào evidence:

```sh
python3 "$SKILL_DIR/scripts/production-guard.py" snapshot "$PROJECT_ROOT" > "$RUN_DIR/test-evidence/inputs/production-before.json"
```

Sau khi làm việc, tạo `production-after.json` bằng cùng lệnh snapshot và kiểm tra:

```sh
python3 "$SKILL_DIR/scripts/production-guard.py" check "$PROJECT_ROOT" --snapshot "$RUN_DIR/test-evidence/inputs/production-before.json"
```

Guard hash mọi file production source set, phát hiện thêm/xóa/thay đổi; bỏ source set
test (kể cả source set test theo variant) và thư mục build/cache/report. Thư mục
symlink chưa được resolve riêng khiến guard dừng có lý do, không âm thầm bỏ source.
Cấu hình test được review diff riêng. Giới hạn
custom roots và trạng thái người dùng thay đổi song song phải ghi rõ; phát hiện
source thay đổi thì không công bố kiểm chứng trên một source ref duy nhất. Không
ghi đè file người dùng hoặc khôi phục production tự động.

## Gates

```sh
python3 "$SKILL_DIR/scripts/validate-coverage.py" "$RUN_DIR" --phase design
python3 "$SKILL_DIR/scripts/validate-coverage.py" "$RUN_DIR" --phase implementation
python3 "$SKILL_DIR/scripts/validate-coverage.py" "$RUN_DIR" --phase execution
```

Execution gate bao gồm các gate trước, yêu cầu snapshots bằng nhau và evidence file
thực sự tồn tại, không rỗng, không thoát khỏi RUN_DIR. Gate tự chạy live guard so
source hiện tại với snapshot before, trả checked_at/unchanged/changed_paths;
không có tùy chọn bỏ qua. Guard không chạy được thì gate không đạt. Lệnh guard check
riêng vẫn có thể dùng để chẩn đoán. Không có Python thì ghi công cụ
validator BLOCKED, vẫn lưu inventory/report và làm các phần độc lập.

Với structured RETEST thêm `--baseline "$BASELINE_RUN_DIR"`: baseline phải là TEST v1/v2
cùng project/module/variant. Validator so ID và định nghĩa gốc; automation/result có
thể cập nhật nhưng expected/checkpoints/owner không thay đổi. Baseline legacy làm
theo workflow tương thích, không tự tạo artifact giả để chạy validator.

RETEST có run ID và thư mục khác baseline sau resolve symlink; baseline reference
và hash phải khớp `--baseline`. Giữ artifact v1 nguyên trạng, tạo run RETEST v2 với
evidence mới. V1 vẫn kiểm được design/implementation; execution v1 không đạt theo
chuẩn mới và yêu cầu run v2. Baseline Markdown legacy không tự chuyển đổi.

Stdout luôn là JSON kết quả/tổng hợp/lỗi. Exit 0: đạt gate được chọn; 1: chưa đạt;
2: lỗi đọc/định dạng đầu vào. Lưu output vào checks khi làm report. Gate đạt không
có nghĩa mọi test PASS, tích hợp thật đã xác minh hoặc toàn bộ source đã được khảo sát.
