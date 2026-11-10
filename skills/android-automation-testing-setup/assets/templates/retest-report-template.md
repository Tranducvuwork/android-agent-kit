# Automation RETEST — <run-id-retest>

Mẫu cấu trúc, không chứa kết quả kiểm thử sẵn. Lưu tại `PROJECT_ROOT/autotesting-reports/<run-id-retest>/report.md`. Đây là snapshot của lần RETEST; file tiến độ được cập nhật là report TEST đầu tiên. Điền dữ liệu thực tế, bỏ hướng dẫn và placeholder trước khi kết thúc.

## Định danh run và baseline

- Chế độ: RETEST.
- Run-id, thời gian bắt đầu/kết thúc, múi giờ: <...>.
- PROJECT_ROOT, app/applicationId, version, module/variant: <...>.
- Source ref/thay đổi chưa commit: <...>.
- Framework/runner, JDK/SDK, thiết bị/emulator nếu cần: <...>.
- Phạm vi yêu cầu và fix được cung cấp: <...>.
- Artifact v2: <baseline {run_dir, sha256}; run ID/thư mục khác TEST gốc, baseline artifact v1/v2 giữ nguyên>.
- Baseline chuẩn: <Link tương đối tới report TEST đầu tiên, run-id gốc và kết quả kiểm tra đúng project/module/variant>.
- Run gần nhất trước lần này: <Run-id/source và link report nếu có>.
- Baseline trước cập nhật: <Link test-evidence/inputs/baseline-before-update.md nếu đã đọc được>.
- Kiểm tra baseline: <Hợp lệ / bị chặn và lý do>.
- Inventory: <N case đã xác định / chưa xác định và lý do>.
- Coverage: <v2 và link artifact / legacy chưa đánh giá coverage toàn app>.
- Skill path/version, production snapshots trước/sau và review cấu hình test: <...>.

## Coverage và index nhóm lần này

- Design/implementation/execution: <Số liệu và output validator; legacy ghi chưa đánh giá>.
- Package/workflow snapshots: <Liên kết trang nhóm mới; mỗi case một owner, tham khảo không đếm lại>.
- Tích hợp fake/sandbox/real và phần chưa xác minh: <...>.

Nếu chưa đọc/xác định được inventory hoặc baseline sai project/variant, báo run bị chặn và điều kiện tiếp tục; không sao chép case mẫu, không dựng inventory mới hoặc giả định 0 case. Không cập nhật baseline không hợp lệ. Nếu riêng case thiếu tiêu chí thì giữ ID với BLOCKED, tiếp tục các case đủ dữ liệu.

## Kết quả lần này

- Case baseline / thuộc phạm vi lần này: <N / N hoặc chưa xác định>.
- Đối chiếu inventory: <Không trùng/thiếu/thêm ID; mục tiêu, bước và expected không đổi / sai lệch cần giải quyết>.
- PASS <N>; FAIL <N>; BLOCKED <N>; NOT_TESTED <N>.
- Mức thực hiện: Có <N>; Một phần <N>; Chưa <N>.
- Số case đổi status so với run ngay trước: <N>.
- Hoàn tất thực hiện: <Có khi không còn BLOCKED/NOT_TESTED và inventory có case / Chưa>.
- Lỗi còn tồn tại/hồi quy và case bị chặn: <Case ID và tác động/điều kiện tiếp tục>.

## Testcase và kết quả

Lặp một mục cho mọi ID baseline, kể cả case từng PASS hoặc chưa chạy lần này. Chép tiêu chí từ baseline, không thay expected bằng kết quả đang quan sát. Không dùng PASS cũ thay bằng chứng mới.

### <AT-001> — <Tên case baseline>

- Lớp test/module/variant: <Theo baseline>.
- Owner/related packages/workflows/screens/checkpoints: <Theo baseline; legacy không tự tạo định nghĩa mới>.
- Mục tiêu: <Theo baseline>.
- Test symbol/scenario/parameter gốc: <Theo baseline>.
- Tiền điều kiện và dữ liệu: <Theo baseline>.
- Bước thực hiện: <Theo baseline>.
- Expected: <Theo baseline>.
- Test symbol/mapping thực hiện lần này: <Đúng symbol gốc hoặc bằng chứng mapping tương đương sau đổi tên>.
- Lệnh/test selection đã chạy: <Lệnh thật hoặc chưa chạy và lý do>.
- Thời gian/môi trường và exit code: <...>.
- Status trước → lần này: <Status gần nhất lúc nạp baseline> → <PASS/FAIL/BLOCKED/NOT_TESTED>.
- Mức thực hiện: <Có/Một phần/Chưa>.
- Actual: <Kết quả mới hoặc phần chưa thực hiện>.
- Execution/runner_result: <Manifest + SHA-256; execution_id, class_name, test_name gồm parameter, ordinal>.
- Bằng chứng mới: <Link tương đối tới test-evidence/checks/ hoặc ảnh; log/runner result đúng case và run>.
- Screenshot lỗi và mọi attempts: <Ảnh đúng case/bước, timing; hoặc lý do unavailable/not_applicable>.
- Lý do và điều kiện tiếp tục: <Bắt buộc khi BLOCKED/NOT_TESTED>.

## Cập nhật baseline

- Đích cập nhật: <Link report TEST đầu tiên>.
- Kết quả: <Chưa cập nhật / Đã cập nhật / Lỗi hoặc xung đột và lý do>.
- Run mới nhất đã ghi vào baseline và thời gian cập nhật: <... hoặc chưa ghi>.
- Phần thay đổi: <Tiến độ hiện tại của mọi case và mốc lịch sử mới>.
- Phần giữ nguyên: <Metadata/tổng hợp TEST ban đầu, inventory/expected, artifact/trang nhóm TEST gốc và toàn bộ lịch sử/bằng chứng cũ>.
- Điều kiện tiếp tục nếu chưa cập nhật: <...>.

Lưu snapshot kết quả này trước khi cập nhật baseline; kiểm tra baseline chưa bị run khác sửa, chuẩn bị bản cập nhật đầy đủ và thay thế qua file tạm cùng thư mục. Cuối run ghi đúng kết quả lưu file. Giữ report RETEST và bằng chứng sau khi kết thúc; các run sau chỉ cập nhật file TEST gốc. Không ghi Đã cập nhật nếu việc ghi baseline thất bại.

## Việc cần tiếp tục và giới hạn

- <Case cần chạy lại và đầu vào/môi trường cần bổ sung>.
- <Case/coverage/expected mới dành cho TEST và baseline mới>.
- <Giới hạn source diff, dữ liệu giả lập, môi trường hoặc output chưa lưu được>.

Tổng bốn status và tổng mức thực hiện bằng tổng inventory; khi inventory chưa xác định phải ghi rõ, không tính tổng giả định. Chỉ ghi hoàn tất thực hiện khi mọi case có kết quả mới PASS/FAIL; vẫn có thể còn FAIL. Phản hồi cuối phải có link report này, baseline và số lượng theo từng status, cùng tình trạng cập nhật baseline thực tế.
