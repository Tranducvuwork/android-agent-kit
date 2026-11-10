# Báo cáo kiểm tra mã nguồn Android — <run-id>

Lưu báo cáo tại `PROJECT_ROOT/qa-reports/<run-id>/report.md`. Run-id theo `<yyyy-mm-dd>-<hhmmss>-<app>-<module>-<variant>-<test|retest>`, có thể thêm hậu tố chống trùng sau chế độ. Bằng chứng cùng run nằm trong `test-evidence/inputs/`, `test-evidence/checks/`, `test-evidence/manifests/`; chỉ tạo phần có dữ liệu và dùng liên kết tương đối từ report.

## Phạm vi và môi trường

- Ngày/giờ bắt đầu và múi giờ: <Khớp thời điểm trong run-id; ghi rõ múi giờ>.
- Chế độ: <TEST/RETEST>.
- Baseline: <Liên kết tương đối/hash/run-id report trước nếu RETEST; không áp dụng nếu TEST>.
- App/package, versionName/versionCode: <...>
- Source/commit/thay đổi chưa commit/module/variant: <...>
- PROJECT_ROOT và đường dẫn output: <Source root và qa-reports/<run-id>/report.md>.
- SKILL_DIR/checklist đã dùng và hash: <...; phân biệt bản nền và rule bổ sung project>
- min/target SDK và cấu hình build: <...>
- Region, consent, remote config: <... hoặc chưa xác định>
- Phương pháp: Chỉ kiểm tra source; <lint/local unit tests đã chạy nếu có>.
- Rule đầu vào và phạm vi policy: <...>
- Giới hạn và đầu vào còn thiếu: <...>

Chỉ tạo testcase source/resources/cấu hình/dependency. Không tạo case chạy app, giao dịch thực tế, kiểm tra APK/AAB, binary alignment hoặc build/cài/chạy artifact. Phần Console, backend, store listing và trải nghiệm thực tế nằm trong giới hạn kết luận, không có testcase riêng. PASS chỉ xác nhận expected whitebox đã ghi.

## Kết quả tổng hợp

- Tổng case source theo dõi: <N>.
- Case source trong phạm vi lần này: <N; với RETEST bằng toàn bộ inventory source baseline>.
- Đối chiếu inventory RETEST: <Số case source baseline; số case thêm/thiếu đều phải bằng 0; không áp dụng nếu TEST>.
- Mức thực hiện trong phạm vi lần này: Có <N>; Một phần <N>; Chưa <N>.
- Status lần này (chỉ case trong phạm vi): PASS <N>; FAIL <N>; BLOCKED <N>; NOT_TESTED <N>; NOT_APPLICABLE <N>.
- Số case thay đổi status sau retest: <N hoặc không áp dụng>.
- Rule/policy đã ánh xạ: <ID → case ID; yêu cầu chưa có case kèm lý do>
- Vấn đề ưu tiên: <Finding ID và tác động>

Tổng case source trong phạm vi lần này bằng toàn bộ inventory source; với RETEST, tập ID phải bằng đúng inventory source baseline. Tổng status lần này và tổng mức thực hiện đều bằng số case trong phạm vi; không tính kết quả lịch sử vào kết quả mới. Case legacy ngoài source và các mục đã nằm riêng trong lịch sử baseline không tính vào inventory và các tổng này. Không loại case source đang có chỉ vì rule bị xóa. “Có” là đã hoàn tất phương pháp source; “Một phần” là đã bắt đầu nhưng chưa hoàn tất, có hoặc không có blocker cụ thể. Nếu chưa đọc được baseline, ghi inventory chưa xác định và chưa retest, không giả định đủ số liệu.

## Phạm vi retest và thay đổi sau fix

Chỉ điền khi RETEST; ghi không áp dụng khi TEST.

- Source cũ → hiện tại và thay đổi chưa commit: <...>.
- Diff/fix được cung cấp và giới hạn nếu không có ref cũ: <...>.
- Inventory baseline → lần này: <Toàn bộ ID source; không thêm, bỏ, tách, gộp hoặc tạo case thay thế>.
- Case bị chặn/chưa hoàn tất: <ID, mức thực hiện, lý do và điều kiện tiếp tục; vẫn thuộc phạm vi lần này>.
- Thay đổi checklist/policy so với baseline: <...; giữ nguyên expected baseline, không generate testcase mới; yêu cầu mới ghi ở việc cần tiếp tục>.

## Danh sách testcase và trạng thái

Lặp lại mục dưới đây cho từng case trong inventory source, kể cả case source chưa thực hiện hoặc không áp dụng. Với RETEST, dùng toàn bộ case source baseline, không tạo case mới và không có nhóm case source được bỏ chọn. Nội dung phải khớp phần chi tiết bên dưới. Không liệt kê case legacy ngoài source tại đây.

- **<TC-001> — <Tên case>**
  - Rule/policy: <DEV-xxx / USR-xxx / GP-NHOM-xxx>.
  - Phương pháp: <Đọc source/resources/cấu hình/dependency; lint/local unit test nếu đã chạy>.
  - Thuộc phạm vi lần này: Có — <Với RETEST: testcase source có sẵn trong baseline>.
  - Đã thực hiện lần này: <Có/Một phần/Chưa>.
  - Status trước: <Status baseline; nếu thiếu ghi rõ, không suy đoán; chưa có nếu TEST>.
  - Status lần này: <PASS/FAIL/BLOCKED/NOT_TESTED/NOT_APPLICABLE>.
  - Status gần nhất: <Status lần này; status cũ giữ trong lịch sử riêng>.
  - Nguồn status gần nhất: <Run-id/source ref lần này>.
  - Bằng chứng hoặc lý do: <file:line, liên kết tương đối tới test-evidence/<nhóm>/<file> của run này hoặc bằng chứng lịch sử, hay lý do chưa thực hiện>.

Ý nghĩa status:

- `PASS`: đã hoàn tất kiểm tra, đạt expected source của case và có bằng chứng.
- `FAIL`: đã hoàn tất kiểm tra, có bằng chứng source trái expected.
- `BLOCKED`: chưa thể hoàn tất vì thiếu đầu vào, nguồn hoặc công cụ cho chính tiêu chí source; ghi phần đã làm và điều kiện tiếp tục. Thiếu APK/thiết bị/tài khoản giao dịch không phải blocker của case source.
- `NOT_TESTED`: case source chưa bắt đầu hoặc chưa hoàn tất mà không có blocker cụ thể; không dùng cho yêu cầu runtime/artifact ngoài phạm vi.
- `NOT_APPLICABLE`: điều kiện áp dụng không đúng với app, có căn cứ cụ thể.

Với status lần này, `PASS`/`FAIL` dùng mức thực hiện `Có`; `BLOCKED`/`NOT_TESTED` dùng `Một phần` hoặc `Chưa` theo bằng chứng; `NOT_APPLICABLE` dùng `Chưa` cho tiêu chí sau khi đã xác định lại không áp dụng trên source hiện tại. Mọi case source baseline phải có status lần này; không dùng nhãn “Không retest” hoặc sao chép PASS cũ thay cho việc kiểm tra lại. Không tạo kết quả PASS/FAIL giả.

## Nguồn policy

### <GP-NHOM-001> — <Yêu cầu>

- Nguồn: <URL chính thức và tên mục cụ thể>
- Truy cập: <Ngày>; hiệu lực: <Ngày hoặc không được công bố rõ>.
- Điều kiện/ngoại lệ và căn cứ áp dụng: <...>
- Yêu cầu source cần kiểm chứng: <Tiêu chí cụ thể trong code/resources/config; phân biệt quy định hiện tại/sắp tới>
- Giới hạn kết luận: <Phần ngoài source chỉ mô tả, không tạo case; không kết luận cả nhóm policy đạt>

## Đối chiếu checklist bắt buộc

- File nền: <Đường dẫn thực tế tới SKILL_DIR/references/dev-checklist.md>
- Rule bổ sung project: <PROJECT_ROOT/checklists/dev-checklist.md hoặc file được chỉ định; không có thì ghi không có>
- Phiên bản/hash nếu có: <...>
- Tổng số rule đọc được: <N>; tổng số ID DEV đã có kết quả: <N>.
- Nếu không đọc được file: `BLOCKED` — <Lý do>; không tuyên bố đã duyệt đầy đủ.

Với TEST, lặp lại khối dưới đây cho mọi ID hiện có trong checklist, giữ cả mục tùy chọn/không áp dụng. Với RETEST, đối chiếu checklist với mapping baseline: rule có case baseline dùng kết quả lần này; rule mới chưa có case ghi rõ chưa có testcase baseline và đề xuất TEST riêng, không sinh case để lấp đủ checklist. Rule bị xóa có case source trong inventory baseline vẫn giữ case và ghi chênh lệch theo workflow retest. Checklist nền hiện có 32 rule, không khôi phục DEV-034/037 từ lịch sử ngoài phạm vi. Không lấy checkbox làm kết quả. Số rule độc lập với số test case.

### <DEV-xxx> — <Tên rule gốc>

- Nhóm, nguồn gốc và kết quả mong đợi source: <Dẫn rule/dòng cụ thể; nội dung gốc runtime chỉ để truy xuất nguồn>
- Trạng thái: <PASS/FAIL/BLOCKED/NOT_TESTED/NOT_APPLICABLE; rule mới chưa có case baseline ghi NOT_TESTED và lý do>
- Case và bằng chứng: <Case ID, file:line hoặc lý do chưa kiểm tra>
- Điều kiện/giới hạn: <Điều kiện áp dụng, đầu vào thiếu cho tiêu chí source và giới hạn kết luận>
- Nguồn kết quả: <Run hiện tại; liệt kê phần bắt buộc bị chặn/chưa hoàn tất hoặc chưa có testcase baseline>

Chỉ kết luận rule `PASS` khi mọi tiêu chí source bắt buộc đã được xác minh. Không lấy thiếu kiểm chứng runtime/artifact làm điều kiện chặn rule source.

## Test case

### <TC-001> — <Tên case>

- Rule/policy: <DEV-xxx / USR-xxx / GP-NHOM-xxx; nguồn rule gốc>
- Phương pháp và phạm vi: <Đọc source/lint/local unit test; module/variant>
- Tiền điều kiện: <...>
- Bước thực hiện: <Các bước có thể tái hiện>
- Mong đợi: <...>
- Thực tế: <Quan sát thực tế hoặc chưa thực hiện>
- Thuộc phạm vi lần này: Có — <Với RETEST: testcase source baseline>
- Đã thực hiện lần này: <Có/Một phần/Chưa; khớp danh sách tổng hợp>
- Status trước → lần này: <Baseline → kết quả lần này; không dùng Không retest>
- Trạng thái gần nhất: <PASS/FAIL/BLOCKED/NOT_TESTED/NOT_APPLICABLE>
- Nguồn status gần nhất: <Run-id/source ref lần này>
- Bằng chứng: <Liên kết tương đối từ report tới test-evidence/<nhóm>/<file> hoặc bằng chứng lịch sử; file:line, lệnh và exit code nếu đã chạy>
- Lý do/giới hạn: <Cần có cho các case chưa xác minh hoặc không áp dụng>

## Lịch sử cập nhật testcase

Với RETEST, giữ các lần trước và thêm một mục cho mọi case source baseline, kể cả case BLOCKED/NOT_TESTED/NOT_APPLICABLE lần này. TEST là mốc đầu tiên nếu chưa có lịch sử.

- **<TC-ID> — <Run-id/thời điểm/source ref>**
  - Status trước → lần này → gần nhất: <...>.
  - Thực tế/bằng chứng mới hoặc lý do bị chặn: <...>.
  - Nguồn status trước: <Baseline/run trước>.

Case legacy ngoài source không có bản ghi “đã retest” mới; giữ lịch sử và đường dẫn bằng chứng đúng về run gốc. Mọi case source đang có trong inventory baseline phải có bản ghi lần này. Baseline cũ có thể nằm trong `reports/android/` với `evidence/`; tính lại liên kết tương đối từ report mới, giữ nguyên file lịch sử.

## Lịch sử ngoài phạm vi source

Chỉ điền khi baseline có case runtime/artifact, yêu cầu Console/backend hoặc các mục đã được lưu riêng ở lịch sử ngoài phạm vi. Không chuyển case source đang có trong inventory baseline sang đây do rule/expected thay đổi. Với TEST không có dữ liệu lịch sử thì bỏ mục này. Các mục này không thuộc inventory source, không xuất hiện lại ở danh sách/chi tiết testcase, không có status lần này và không tính vào summary.

- **<Case ID cũ>** — <Mục tiêu cũ, status lịch sử và nguồn run>.
  - Baseline/bằng chứng: <Liên kết tương đối; không sửa file cũ>.
  - Lý do ngoài inventory: <Ngoài source hoặc đã nằm trong lịch sử ngoài phạm vi baseline>.
  - Liên kết case thay thế từ lịch sử: <Chỉ giữ ID/link có sẵn nếu có; không tạo case thay thế trong RETEST>.
  - Finding cũ: <Giữ phần chưa xác minh còn mở; không đóng chỉ vì PASS source hoặc loại khỏi phạm vi>.

## Findings

### <F-001> — <Vấn đề>

- Mức độ và tác động: <critical/high/medium/low; giải thích>
- Case/module/variant bị ảnh hưởng: <...>
- Cách tái hiện và bằng chứng: <...>
- Điều khoản policy: <Link cụ thể nếu là policy finding>
- Đề xuất xử lý: <...>
- Kiểm tra lại: <Chưa chạy hoặc run/case/bằng chứng sau sửa>
- Trạng thái finding: <Còn mở/Đã xác minh sửa xong; ghi rõ nếu chưa retest hoặc còn bị chặn>

## Việc cần tiếp tục

- <Đầu vào cần bổ sung, case cần chạy và điều kiện để tiếp tục>
- <Yêu cầu/checklist/policy mới chưa có testcase baseline; đề xuất đợt TEST riêng, không generate case trong RETEST>

Với RETEST, chỉ báo hoàn tất kiểm tra lại toàn bộ khi không còn case BLOCKED/NOT_TESTED và mọi case đã được kiểm tra lại hoặc xác minh không áp dụng bằng bằng chứng mới.

Không kết luận Google Play sẽ duyệt app dựa trên báo cáo này.
