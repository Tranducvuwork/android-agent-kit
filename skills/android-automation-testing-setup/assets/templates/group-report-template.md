# <Package hoặc workflow> — <run-id>

Mẫu dùng cho `packages/<package-path>/report.md` hoặc `workflows/<workflow-id>/report.md`.
Thay placeholder, tính lại mọi liên kết theo vị trí trang nhóm.

- Owner: <package/workflow và ID>.
- Report đầu mối, source/module/variant: <Liên kết và định danh>.
- Package/màn hình/workflow liên quan: <Các liên kết; case tham khảo không cộng lại>.
- Tổng case owner nhóm: <N>; PASS <N>; FAIL <N>; BLOCKED <N>; NOT_TESTED <N>.
- Thiết kế/triển khai/thực thi; mức xác minh fake/sandbox/real: <Thực tế>.

## Testcase thuộc nhóm

### <AT-001> — <Tên case>

- Mục tiêu, preconditions/dữ liệu: <Theo định nghĩa baseline>.
- Layer và test symbol/scenario: <...>.
- Bước và expected: <Theo định nghĩa baseline; checkpoint có action/expected riêng>.
- Package/screens/workflow liên quan: <...>.
- Status trước → lần này, mức thực hiện: <...>.
- Actual/checkpoint thất bại: <...>.
- Execution mapping: <execution_id/class_name/test_name/ordinal; link manifest và raw result>.
- Attempts: <Lệnh/selector/run/source/device/thời gian/kết quả từng attempt và log>.
- Screenshot lỗi: <Liên kết/hiển thị PNG đúng case/attempt/checkpoint, timing;
  hoặc unavailable/not_applicable và lý do>.
- Chẩn đoán: <Source nghi vấn và bằng chứng; ghi rõ suy luận nếu chưa xác nhận>.
- Điều kiện tiếp tục: <Blocker hoặc phần chưa thực hiện; không tự sửa app>.

## Case tham khảo ở nhóm khác

- <Liên kết tới trang chi tiết chính của case; không sao chép hoặc đếm lần hai>.

Trang nhóm là snapshot của run. RETEST ghi trang nhóm mới, giữ expected/ID và evidence
cũ; report TEST gốc cập nhật index/tiến độ tới snapshot mới nhất và thêm lịch sử.
