# Tình huống kiểm tra report và baseline automation

Đây là fixture giả lập để walkthrough workflow và template, không phải kết quả kiểm thử app Android. Kết quả runner/log giả lập phải được ghi rõ là fixture trong report; không dùng chúng để khẳng định app thực tế PASS. Chạy thử trong project fixture ở thư mục tạm, không tạo báo cáo giả trong project người dùng.

## Chuỗi TEST → RETEST 1 → RETEST 2

Định danh fixture: app `fixture`, module `app`, variant `debug`, múi giờ `Asia/Ho_Chi_Minh`. Tạo bốn case AT-001..AT-004 với expected cố định, trong đó AT-003 là instrumented test, các case khác độc lập với thiết bị.

- TEST: AT-001 PASS, AT-002 FAIL, AT-003 BLOCKED vì thiếu emulator, AT-004 NOT_TESTED vì chưa chạy trong phạm vi thời gian lần đầu. Tổng 4; mỗi status có 1 case.
- RETEST 1: AT-001 FAIL (hồi quy), AT-002 PASS (fix được xác minh), AT-003 PASS (emulator đã có), AT-004 NOT_TESTED (chưa chạy, không có blocker). Tổng PASS 2, FAIL 1, BLOCKED 0, NOT_TESTED 1; 3 case đổi status; chưa hoàn tất thực hiện.
- RETEST 2: AT-001 PASS, AT-002 PASS, AT-003 PASS, AT-004 PASS. Tổng PASS 4, các status khác 0; 2 case đổi status so với RETEST 1; hoàn tất thực hiện.

- [ ] Mỗi run có report đúng format và bằng chứng fixture riêng.
- [ ] Chỉ report TEST đầu tiên nhận cập nhật tiến độ; không có file baseline riêng.
- [ ] Inventory/expected và metadata/tổng TEST ban đầu không thay đổi.
- [ ] Baseline cuối có đủ ba mốc cho cả bốn case, giữ nguyên actual và bằng chứng từng mốc.
- [ ] Report RETEST 1 vẫn giữ số liệu 2/1/0/1 sau RETEST 2.
- [ ] Liên kết bằng chứng trong baseline và từng report trỏ đúng run, không nhầm đường dẫn tương đối.
- [ ] Tổng status/mức thực hiện khớp inventory; không dùng PASS cũ cho AT-001 hoặc AT-004.

## Baseline và phạm vi

- [ ] Thiếu baseline: lưu report RETEST bị chặn, inventory chưa xác định, không dựng case hay sửa file khác.
- [ ] Baseline sai app/module/variant: từ chối cập nhật, ghi lý do và yêu cầu baseline đúng.
- [ ] Có hai baseline phù hợp: hỏi lựa chọn, không chọn dựa trên mtime.
- [ ] Đầu vào là report RETEST: theo liên kết về report TEST gốc, giữ chuỗi lịch sử.
- [ ] ID trùng hoặc thiếu inventory: không cập nhật baseline như thể đã chạy đủ; ghi lỗi dữ liệu.
- [ ] Inventory đủ nhưng một case thiếu expected: giữ ID với BLOCKED, không tự bổ sung tiêu chí; tiếp tục case khác.
- [ ] Có case mới hoặc expected thay đổi: ghi việc cần TEST/baseline mới, không thêm/bớt case trong RETEST.
- [ ] Chỉ phân tích/thiết lập: không chạy test, case chưa chạy là NOT_TESTED và không báo đạt assertion.

## Bằng chứng và lỗi output

- [ ] Thiếu emulator chặn AT-003 nhưng không chặn các unit test độc lập.
- [ ] Build/runner không khởi động: case phụ thuộc BLOCKED; không chuyển mọi case thành FAIL.
- [ ] Case thực thi gặp assertion/exception/crash có bằng chứng từ runner: FAIL.
- [ ] Runner skip case: BLOCKED khi có blocker cụ thể; NOT_TESTED khi chỉ bị bỏ qua.
- [ ] Log/XML tồn dư hoặc task up-to-date không có bằng chứng thực thi mới: không gán PASS mới.
- [ ] Thư mục run-id đã tồn tại: tạo timestamp mới theo đúng format, giữ run cũ.
- [ ] Baseline thay đổi trong lúc chạy: giữ report mới, không ghi đè baseline, báo xung đột cập nhật.
- [ ] Ghi baseline thất bại: report RETEST còn giữ kết quả, ghi chưa cập nhật/lỗi và điều kiện tiếp tục.
- [ ] Không ghi được report: phản hồi nói rõ output chưa lưu, không báo cập nhật tiến độ thành công.
- [ ] Test screenshot thất bại: giữ ảnh chuẩn/expected; không tự regenerate golden để làm PASS.

## Coverage toàn app và nhóm test

- [ ] Dùng hai app fixture khác package/nghiệp vụ/DI, ví dụ trình ghi chú và danh mục hàng; discovery dựa vào source, không yêu cầu package/màn hình của một app cụ thể.
- [ ] Đặt một Activity, click handler hoặc receiver ngoài danh mục đã chọn: lượt đối chiếu source phải phát hiện workflow chưa khảo sát, giữ discovery chưa hoàn tất.
- [ ] Mọi case cũ PASS nhưng nhánh lỗi/validation mới chưa mapping: design/execution gate chưa đạt.
- [ ] Expected chưa rõ: obligation còn trong draft, không chốt baseline hay đổi expected theo bug đang quan sát.
- [ ] Package chứa model/constants được liên kết tới hành vi sử dụng hoặc có lý do không áp dụng; không tạo test chỉ để tăng số lượng.
- [ ] Component test mirror package; dependency fake không tự biến thành journey. Test qua nhiều màn hình/cross-package có owner workflow, checkpoint và chạy riêng được.
- [ ] Từ nhóm khác liên kết tới cùng AT-ID: totals chỉ cộng một lần.
- [ ] Thiếu test seam production: giữ BLOCKED và điều kiện tiếp tục, không sửa interface/DI/source/manifest/resource/debug app.
- [ ] Production dirty trước run được giữ nguyên; guard phát hiện file mới/xóa/đổi sau run. Cấu hình runner/dependency chỉ có diff test-only đã review.
- [ ] Fake PASS cho billing/backend không được báo đã xác minh tích hợp thật; mức fake/sandbox/real tách riêng.
- [ ] Legacy baseline thiếu artifact vẫn RETEST theo định nghĩa cũ; coverage full-app chưa đánh giá, không tự mở rộng inventory.

## Screenshot lỗi và tái hiện

- [ ] Assertion UI fail trong ActivityScenario: capture xảy ra trước teardown, PNG/log gắn đúng run/case/attempt/checkpoint.
- [ ] Journey fail ở bước giữa: report chỉ ra checkpoint và source nghi vấn, có ảnh gần lỗi khi capture được.
- [ ] Instrumentation process crash: host giữ log, ảnh launcher sau crash được ghi after_crash, không mô tả như UI trước crash.
- [ ] Screenshot/pull bị lỗi: original assertion vẫn là lỗi chính; capture error ghi riêng, status vẫn FAIL.
- [ ] Lần đầu thiếu ảnh: tối đa một attempt tái hiện cùng fixture/config/source để lấy evidence, giữ attempt đầu. Retry PASS không xóa FAIL cùng run.
- [ ] FLAG_SECURE/device disconnect/không tái hiện được: unavailable có lý do; JVM không UI: not_applicable có lý do.
- [ ] Ảnh của case/run khác, link thoát thư mục run, checkpoint sai hoặc file không phải PNG: validator từ chối.

## Coverage v2, collector và live guard

- [ ] PNG chứa `..` trỏ sang case khác, symlink hoặc hardlink dùng lại bị chặn; hai file ảnh độc lập giống nội dung vẫn hợp lệ.
- [ ] XML skipped nhưng artifact khai PASS, parameter/symbol/module/variant sai hoặc normalized results mâu thuẫn raw: gate không đạt.
- [ ] XML flakyFailure/rerunFailure và retries ở execution khác được giữ; không bỏ invocation khỏi catalog hoặc bỏ completed attempt để che FAIL.
- [ ] Collector thu nhiều XML mới, bỏ output cũ không thay đổi, giữ log/exit code khi command lỗi; timeout/lỗi khởi động giữ manifest riêng.
- [ ] Command argv có ký tự shell không bị thực thi như shell; Gradle thiếu flag rerun/no-cache bị chặn trước khi chạy.
- [ ] Instrumentation chọn serial cụ thể; ignored/assumption không PASS, process crash thiếu terminal không tự thành FAIL cho mọi case.
- [ ] Raw/manifest bị sửa sau capture hoặc mapping result bị dùng lại khiến gate không đạt; hash không được mô tả như chứng thực chống giả mạo.
- [ ] RETEST dùng run ID/thư mục khác TEST (kể cả symlink alias), có baseline hash và evidence mới; baseline v1 giữ nguyên và được dùng cho RETEST v2.
- [ ] Execution v1 yêu cầu run v2; design/implementation v1 vẫn đọc được. Hai snapshot cũ giống nhau nhưng source hiện tại thêm/xóa/sửa thì live gate trả changed_paths.
- [ ] Gói cài copy/symlink chứa đủ shared parser và collector; hai CLI entrypoint chạy từ project khác không phụ thuộc repo nguồn.

Các tình huống cần Android/host crash capture là walkthrough trên fixture được phép,
không được đánh dấu đã chạy thiết bị chỉ dựa vào Python tests. Unit tests tự động
kiểm tra hợp đồng artifact/guard; không thay thế khảo sát source hay instrumentation.
