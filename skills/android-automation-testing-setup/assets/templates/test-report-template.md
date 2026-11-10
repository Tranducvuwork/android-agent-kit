# Automation TEST và baseline tiến độ — <run-id-test>

Mẫu cấu trúc, không chứa kết quả kiểm thử sẵn. Lưu tại `PROJECT_ROOT/autotesting-reports/<run-id-test>/report.md`. Điền dữ liệu thực tế; bỏ hướng dẫn và placeholder trước khi kết thúc. Giữ metadata, inventory và lịch sử TEST ban đầu khi cập nhật tiến độ sau RETEST. Nếu inventory chưa xác định, ghi rõ phần thiếu, không lặp case mẫu và không coi report là baseline hợp lệ.

## Định danh TEST ban đầu — giữ nguyên

- Chế độ: TEST.
- Run-id, thời gian bắt đầu/kết thúc, múi giờ: <...>.
- PROJECT_ROOT, app/applicationId, version: <...>.
- Module/variant và source ref/thay đổi chưa commit: <...>.
- Phạm vi được yêu cầu và công việc thực sự thực hiện: <...>.
- Framework/runner, JDK/SDK và thiết bị/emulator nếu cần: <...>.
- Skill path/version, branch/source và trạng thái production trước run: <...>.
- Phạm vi coverage: <full_app/focused; discovery sources, exclusions và gaps>.
- Inventory: <Đã xác định đầy đủ N case / chưa xác định và lý do / không có case trong phạm vi>.
- Baseline hợp lệ: <Có khi inventory đầy đủ, có case / Không và lý do>.

## Kết quả TEST ban đầu — giữ nguyên

- Tổng case: <N hoặc chưa xác định>.
- PASS <N>; FAIL <N>; BLOCKED <N>; NOT_TESTED <N>.
- Mức thực hiện: Có <N>; Một phần <N>; Chưa <N>.
- Kết quả từng case và bằng chứng ban đầu: <Dẫn mốc TEST đầu tiên trong lịch sử bên dưới>.

## Coverage và index nhóm

- Executions: <Link manifest/hash do collector thu; raw results được validator parse lại; thời gian run bắt buộc>.
- Artifact: <Link test-evidence/inputs/coverage.json; phiên bản 2>.
- Thiết kế: <Obligations đã mapping / tổng applicable; gaps chưa rõ expected>.
- Triển khai: <Số case có automation / tổng case>.
- Thực thi: <Số case có PASS/FAIL mới / tổng case; link output validator từng gate>.
- Production guard: <Link snapshots trước/sau và kết quả live gate checked_at/changed_paths; diff cấu hình test đã review>.
- Mức xác minh tích hợp: <Workflow dùng fake/sandbox/real và phần chưa xác minh>.
- Package: <Liên kết packages/package-path/report.md, số case owner duy nhất>.
- Workflow: <Liên kết workflows/workflow-id/report.md, packages/screens liên quan>.

Mỗi case có một trang chi tiết chính theo mẫu nhóm. Nhóm khác chỉ liên kết tham khảo.
Trang nhóm và artifact TEST gốc giữ nguyên sau khi khóa baseline.

## Inventory testcase gốc — khóa sau TEST

Lặp một mục cho mỗi case, không lặp lại khi thêm lịch sử RETEST. ID có dạng AT-001, AT-002, ...; không lấy phương pháp source review làm bằng chứng automation đã chạy.

### <AT-001> — <Tên case>

- Lớp test/module/variant: <unit/Espresso/database/screenshot/navigation/E2E; module; variant>.
- Owner và trang chi tiết: <package/workflow, ID và liên kết nhóm chính>.
- Package/workflow/screens liên quan, obligation IDs: <...>.
- Mục tiêu: <...>.
- Test symbol/scenario/parameter gốc: <Class.method, scenario hoặc chưa triển khai>.
- Tiền điều kiện và dữ liệu: <...>.
- Bước thực hiện: <Các bước kiểm chứng được>.
- Expected: <Assertion/hành vi/ảnh chuẩn cần đạt; không đổi trong RETEST>.
- Checkpoints: <ID, action, expected; workflow có ít nhất hai checkpoint hành vi>.

## Tiến độ hiện tại — cập nhật sau mỗi run

Lần TEST đầu lấy kết quả TEST; sau mỗi RETEST thay toàn bộ phần này bằng kết quả của run mới, kể cả BLOCKED/NOT_TESTED. Không cộng PASS lịch sử vào PASS lần này.

- Run/source/môi trường mới nhất và thời gian: <...>.
- Chế độ mới nhất: <TEST/RETEST>.
- Report mới nhất: <Liên kết tương đối; lần TEST đầu là report.md hiện tại>.
- Tổng inventory: <N>.
- PASS <N>; FAIL <N>; BLOCKED <N>; NOT_TESTED <N>.
- Mức thực hiện: Có <N>; Một phần <N>; Chưa <N>.
- Số case đổi status so với run ngay trước: <N hoặc chưa có run trước>.
- Hoàn tất thực hiện: <Có khi không còn BLOCKED/NOT_TESTED và inventory có case / Chưa>.
- Lỗi còn tồn tại và việc cần tiếp tục: <Case ID, tác động hoặc điều kiện tiếp tục>.

Lặp một mục cho mọi ID trong inventory:

- **<AT-001> — <Tên case>**
  - Status trước → hiện tại: <Chưa có nếu TEST đầu / status run ngay trước> → <PASS/FAIL/BLOCKED/NOT_TESTED>.
  - Mức thực hiện: <Có/Một phần/Chưa>.
  - Actual: <Kết quả chạy hoặc phần chưa thực hiện>.
  - Nguồn kết quả: <Run-id/source/môi trường mới nhất>.
  - Bằng chứng: <Link tương đối tới log/kết quả runner/ảnh của đúng run; mapping test symbol hiện tại nếu đổi tên>.
  - Screenshot lỗi: <Link ảnh đúng case/attempt/checkpoint và timing; hoặc unavailable/not_applicable kèm lý do>.
  - Lý do và điều kiện tiếp tục: <Bắt buộc khi BLOCKED/NOT_TESTED>.

## Lịch sử các lần chạy — chỉ thêm mốc mới

Lần đầu ghi mốc TEST và mọi case. Mỗi RETEST thêm mốc mới, giữ nguyên tất cả mốc cũ và các đường dẫn bằng chứng lịch sử. Nội dung mốc TEST là kết quả ban đầu được giữ nguyên dù phần tiến độ hiện tại đã thay đổi.

### <run-id> — <TEST/RETEST>

- Thời gian và múi giờ: <...>.
- Source/thay đổi chưa commit/module/variant/môi trường: <...>.
- Report run này: <Link tương đối>.
- Lệnh đã chạy: <Lệnh, test selection, thời gian, exit code và link log; không chạy thì ghi rõ>.
- Tổng: <N>; PASS <N>; FAIL <N>; BLOCKED <N>; NOT_TESTED <N>.
- **<AT-001>**
  - Status trước → lần này: <...> → <PASS/FAIL/BLOCKED/NOT_TESTED>.
  - Mức thực hiện và actual: <...>.
  - Bằng chứng mới hoặc lý do/điều kiện tiếp tục: <...>.

## Việc cần tiếp tục

- <Case chưa hoàn tất và điều kiện chạy lại>.
- <Coverage/case/expected mới cần TEST và baseline mới; không đưa vào inventory này qua RETEST>.
- <Giới hạn môi trường, dữ liệu giả lập và phần chưa được kiểm chứng>.
- <Lỗi app/checkpoint/source nghi vấn; chỉ ghi nhận, không sửa production>.

Tổng bốn status và tổng mức thực hiện đều bằng tổng inventory, tính riêng cho từng run. Baseline không phải reference image của screenshot framework. Báo cáo chỉ xác nhận những testcase thực sự đã chạy trong môi trường ghi nhận.
